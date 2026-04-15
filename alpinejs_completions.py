from __future__ import annotations
import re
from sublime import View, CompletionList, CompletionItem, Region, AutoCompleteFlags
from sublime_plugin import EventListener
from typing import Dict, List, Set, Tuple, Optional
from sublime_types import Point, KindId


class AlpineJsCompletions(EventListener):
    def file_uses_alpine(self, view: View) -> bool:
        content = view.substr(Region(0, view.size()))
        return (
            'alpinejs' in content.lower()
            or 'alpine.' in content.lower()
            or bool(re.search(r'\b(?:x-data|x-init|x-show|x-bind|x-on|x-text|x-html|x-model|x-effect)\b', content))
        )

    def is_inside_document_add_event_listener_event(self, view: View, pt: Point) -> bool:
        limit = max(0, pt - 500)
        text = view.substr(Region(limit, pt))
        match = re.search(r'document\.addEventListener\(\s*(["\'])', text)
        if not match:
            return False

        quote_type = match.group(1)
        return quote_type not in text[match.end():]

    def is_inside_top_level_alpine_data_object(self, view: View, pt: Point) -> bool:
        content = view.substr(Region(0, view.size()))
        pattern = re.compile(r'Alpine\.data\(\s*(["\'])([\w-]+)\1\s*,', re.DOTALL)

        for match in pattern.finditer(content):
            search_start = match.end()
            object_start = content.find('({', search_start)
            if object_start == -1:
                continue

            opening_brace_index = object_start + 1
            closing_brace_index = self.find_matching_brace(content, opening_brace_index)
            if closing_brace_index == -1 or not (opening_brace_index < pt < closing_brace_index):
                continue

            depth = 1
            string_quote: Optional[str] = None
            escaped = False

            for char in content[opening_brace_index + 1:pt]:
                if escaped:
                    escaped = False
                    continue

                if string_quote:
                    if char == '\\':
                        escaped = True
                    elif char == string_quote:
                        string_quote = None
                    continue

                if char in ('"', "'", '`'):
                    string_quote = char
                elif char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1

            return string_quote is None and depth == 1

        return False

    def get_dispatched_custom_event_names(self, view: View) -> Set[str]:
        content = view.substr(Region(0, view.size()))
        return set(re.findall(r'\$dispatch\(\s*["\']([\w:-]+)["\']', content))

    def get_current_open_tag(self, view: View, pt: Point) -> Optional[Tuple[int, int, str, str, bool]]:
        content = view.substr(Region(0, view.size()))
        current_tag: Optional[Tuple[int, int, str, str, bool]] = None

        for tag_start, tag_end, is_closing, tag_name, attrs, self_closing in self.iter_html_tags(content):
            if tag_start > pt:
                break

            if not is_closing and tag_start <= pt <= tag_end:
                current_tag = (tag_start, tag_end, tag_name.lower(), attrs, self_closing)
                break

        return current_tag

    def get_descendant_custom_event_names(self, view: View, pt: Point) -> Set[str]:
        current_tag = self.get_current_open_tag(view, pt)
        if current_tag is None:
            return set()

        current_tag_start, current_tag_end, current_tag_name, _, self_closing = current_tag
        if self_closing:
            return set()

        content = view.substr(Region(0, view.size()))
        depth = 0
        subtree_end: Optional[int] = None
        entered_current_tag = False

        for tag_start, tag_end, is_closing, tag_name, _, tag_self_closing in self.iter_html_tags(content):
            tag_name = tag_name.lower()

            if not entered_current_tag:
                if tag_start == current_tag_start and not is_closing:
                    entered_current_tag = True
                    depth = 1
                continue

            if is_closing and tag_name == current_tag_name:
                depth -= 1
                if depth == 0:
                    subtree_end = tag_start
                    break
                continue

            if not is_closing and tag_name == current_tag_name and not tag_self_closing:
                depth += 1

        if subtree_end is None or subtree_end <= current_tag_end:
            return set()

        subtree_content = content[current_tag_end:subtree_end]
        return set(re.findall(r'\$dispatch\(\s*["\']([\w:-]+)["\']', subtree_content))

    def iter_html_tags(self, content: str):
        index = 0

        while index < len(content):
            if content[index] != '<':
                index += 1
                continue

            tag_start = index
            index += 1
            quote_type: Optional[str] = None

            while index < len(content):
                char = content[index]
                if quote_type:
                    if char == quote_type:
                        quote_type = None
                else:
                    if char in ('"', "'"):
                        quote_type = char
                    elif char == '>':
                        tag_end = index + 1
                        tag_content = content[tag_start + 1:index].strip()

                        if tag_content and not tag_content.startswith(('!', '?')):
                            is_closing = tag_content.startswith('/')
                            if is_closing:
                                tag_content = tag_content[1:].lstrip()

                            self_closing = tag_content.endswith('/')
                            if self_closing:
                                tag_content = tag_content[:-1].rstrip()

                            tag_name_match = re.match(r'([\w:-]+)', tag_content)
                            if tag_name_match:
                                tag_name = tag_name_match.group(1)
                                attrs = tag_content[tag_name_match.end():]
                                yield tag_start, tag_end, is_closing, tag_name, attrs, self_closing

                        index = tag_end
                        break

                index += 1

    def get_current_tag_context(self, view: View, pt: Point) -> Optional[str]:
        limit = max(0, pt - 5000)
        text = view.substr(Region(limit, pt))
        tag_start: Optional[int] = None
        in_tag = False
        quote_type: Optional[str] = None

        for index, char in enumerate(text):
            if not in_tag:
                if char == '<':
                    in_tag = True
                    tag_start = index
                continue

            if quote_type:
                if char == quote_type:
                    quote_type = None
                continue

            if char in ('"', "'"):
                quote_type = char
            elif char == '>':
                in_tag = False
                tag_start = None

        if not in_tag or tag_start is None:
            return None

        return text[tag_start:]

    def get_current_alpine_attribute_context(self, view: View, pt: Point) -> Tuple[Optional[str], bool, str]:
        tag_context = self.get_current_tag_context(view, pt)
        if tag_context is None:
            return None, False, ''

        matches = list(re.finditer(r'([\w\.:@-]+)\s*=\s*(["\'])', tag_context))

        for match in reversed(matches):
            attr_name = match.group(1)
            quote_type = match.group(2)
            start_pos = match.end()
            content_after_attr = tag_context[start_pos:]

            if quote_type not in content_after_attr:
                is_alpine = attr_name.startswith(('x-', '@', ':'))
                return (attr_name if is_alpine else None), True, content_after_attr

        return None, False, ''

    def merge_member_maps(self, *member_maps: Dict[str, str]) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        for member_map in member_maps:
            merged.update(member_map)
        return merged

    def find_matching_brace(self, content: str, opening_brace_index: int) -> int:
        depth = 0

        for index in range(opening_brace_index, len(content)):
            char = content[index]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return index

        return -1

    def get_registered_data_definitions(self, view: View) -> Dict[str, Dict[str, str]]:
        content = view.substr(Region(0, view.size()))
        definitions: Dict[str, Dict[str, str]] = {}
        pattern = re.compile(r'Alpine\.data\(\s*(["\'])([\w-]+)\1\s*,', re.DOTALL)

        for match in pattern.finditer(content):
            data_name = match.group(2)
            search_start = match.end()

            object_start = content.find('({', search_start)
            if object_start == -1:
                continue

            opening_brace_index = object_start + 1
            closing_brace_index = self.find_matching_brace(content, opening_brace_index)
            if closing_brace_index == -1:
                continue

            block_content = content[opening_brace_index + 1:closing_brace_index]
            definitions[data_name] = self.extract_x_data_members(block_content)

        return definitions

    def get_registered_store_definitions(self, view: View) -> Dict[str, Dict[str, str]]:
        content = view.substr(Region(0, view.size()))
        definitions: Dict[str, Dict[str, str]] = {}
        pattern = re.compile(r'Alpine\.store\(\s*(["\'])([\w-]+)\1\s*,', re.DOTALL)

        for match in pattern.finditer(content):
            store_name = match.group(2)
            search_start = match.end()

            object_start = content.find('{', search_start)
            if object_start == -1:
                continue

            closing_brace_index = self.find_matching_brace(content, object_start)
            if closing_brace_index == -1:
                continue

            block_content = content[object_start + 1:closing_brace_index]
            definitions[store_name] = self.extract_x_data_members(block_content)

        return definitions

    def get_registered_data_names(self, view: View) -> Set[str]:
        return set(self.get_registered_data_definitions(view).keys())

    def get_registered_store_names(self, view: View) -> Set[str]:
        return set(self.get_registered_store_definitions(view).keys())

    def resolve_x_data_members(self, block_content: str, registered_data: Dict[str, Dict[str, str]]) -> Dict[str, str]:
        stripped_content = block_content.strip()
        if not stripped_content:
            return {}

        if stripped_content.startswith('{'):
            return self.extract_x_data_members(stripped_content)

        data_reference_match = re.match(r'^([\w-]+)\s*(?:\([^)]*\))?$', stripped_content)
        if data_reference_match:
            return dict(registered_data.get(data_reference_match.group(1), {}))

        return {}

    def extract_x_data_members(self, block_content: str) -> Dict[str, str]:
        members: Dict[str, str] = {}

        for prop in re.findall(r'(\w+)\s*:', block_content):
            members[prop] = 'property'

        for accessor_type, accessor_name in re.findall(r'\b(get|set)\s+(\w+)\s*\([^)]*\)\s*\{', block_content):
            members[accessor_name] = 'property'

        for method_name in re.findall(r'(\w+)\s*\([^)]*\)\s*\{', block_content):
            if method_name not in {'get', 'set'}:
                members[method_name] = 'method'

        return members

    def get_active_x_data_members(self, view: View, pt: Point) -> Dict[str, str]:
        """
        Encuentra las propiedades x-data visibles en la posición actual.
        Respeta el scope HTML: incluye el x-data actual y sus ancestros abiertos,
        pero no los x-data de nodos hijos o hermanos.
        """
        content = view.substr(Region(0, view.size()))
        registered_data = self.get_registered_data_definitions(view)
        x_data_pattern = re.compile(r'x-data\s*=\s*(?P<q>["\'])(.*?)(?P=q)', re.DOTALL)
        stack: List[Tuple[str, Dict[str, str]]] = []

        for tag_start, tag_end, is_closing, tag_name, attrs, self_closing in self.iter_html_tags(content):
            if tag_start > pt:
                break
            tag_name = tag_name.lower()

            if is_closing:
                for index in range(len(stack) - 1, -1, -1):
                    if stack[index][0] == tag_name:
                        del stack[index:]
                        break
            else:
                members: Dict[str, str] = {}
                x_data_match = x_data_pattern.search(attrs)
                if x_data_match:
                    members = self.resolve_x_data_members(x_data_match.group(2), registered_data)

                stack.append((tag_name, members))

                if self_closing or attrs.strip().endswith('/'):
                    stack.pop()

            if tag_start <= pt < tag_end:
                break

        active_members: Dict[str, str] = {}
        for _, members in stack:
            active_members = self.merge_member_maps(active_members, members)

        return active_members

    def get_current_alpine_attribute(self, view: View, pt: Point) -> Tuple[Optional[str], bool]:
        """
        Encuentra el nombre del atributo Alpine en el que se encuentra el cursor.
        Retorna (nombre_del_atributo, esta_dentro_de_comillas).
        """
        attr_name, is_inside, _ = self.get_current_alpine_attribute_context(view, pt)
        return attr_name, is_inside

    def is_inside_alpine_expression_string(self, view: View, pt: Point) -> bool:
        attr_name, is_inside, content_before_cursor = self.get_current_alpine_attribute_context(view, pt)
        if not is_inside or not attr_name:
            return False

        string_quote: Optional[str] = None
        escaped = False

        for char in content_before_cursor:
            if escaped:
                escaped = False
                continue

            if string_quote:
                if char == '\\':
                    escaped = True
                elif char == string_quote:
                    string_quote = None
                continue

            if char in ('"', "'"):
                string_quote = char

        return string_quote is not None

    def get_active_arrow_function_vars(self, view: View, pt: Point) -> Set[str]:
        attr_name, is_inside, content_before_cursor = self.get_current_alpine_attribute_context(view, pt)
        if not is_inside or not attr_name:
            return set()

        vars = set()
        pattern = re.compile(r'(?:\(([^)]*)\)|([A-Za-z_$][\w$]*))\s*=>')

        for match in pattern.finditer(content_before_cursor):
            tuple_params, single_param = match.groups()
            if single_param:
                vars.add(single_param)
            elif tuple_params:
                for param in tuple_params.split(','):
                    param_name = param.strip()
                    if param_name:
                        vars.add(param_name)

        return vars

    def get_active_iteration_vars(self, view: View, pt: Point) -> Set[str]:
        """
        Encuentra las variables de x-for activas en la posición actual.
        """
        vars = set()
        prefix_content = view.substr(Region(0, pt))
        matches = list(re.finditer(r'<template\s+[^>]*x-for\s*=\s*["\']\s*(?:\(([^)]+)\)|(\w+))\s+in', prefix_content, re.IGNORECASE))
        
        for match in reversed(matches):
            between_content = prefix_content[match.end():]
            opens = between_content.lower().count('<template')
            closes = between_content.lower().count('</template')
            if closes <= opens:
                tuple_match, single_match = match.groups()
                if single_match: vars.add(single_match)
                if tuple_match:
                    for v in tuple_match.split(','): vars.add(v.strip())
        return vars

    def on_query_completions(
        self,
        view: View,
        prefix: str,
        locations: List[Point],
    ) -> CompletionList:
        pt = locations[0]
        line_prefix = view.substr(Region(view.line(pt).a, pt))
        
        kind_directive = [KindId.NAMESPACE, 'd', 'Alpine.js Directive']
        kind_data = [KindId.NAMESPACE, 'd', 'Alpine.js Data']
        kind_store = [KindId.NAMESPACE, 's', 'Alpine.js Store']
        kind_attribute = [KindId.MARKUP, 'a', 'Bindable Attribute']
        kind_custom_event = [KindId.FUNCTION, 'c', 'Custom Event']
        kind_method = [KindId.FUNCTION, 'm', 'Alpine.js Method']
        kind_property = [KindId.VARIABLE, 'p', 'Alpine.js Property']
        kind_variable = [KindId.VARIABLE, 'v', 'Alpine.js Variable']
        kind_modifier = [KindId.KEYWORD, 'm', 'Modifier']
        kind_event = [KindId.FUNCTION, 'e', 'Event']

        # 1. CONTEXTO: CDN
        if re.search(r'<script\s+[^>]*src=["\'][^"\']*$', line_prefix):
            return CompletionList([CompletionItem(
                "https://cdn.jsdelivr.net/npm/alpinejs@3.15.11/dist/cdn.min.js",
                kind=[KindId.MARKUP, 'c', 'CDN'],
                annotation='Alpine.js v3.15.11'
            )])

        # 1.25 CONTEXTO: document.addEventListener('...')
        if self.file_uses_alpine(view) and self.is_inside_document_add_event_listener_event(view, pt):
            lifecycle_events = [
                CompletionItem('alpine:init', kind=kind_custom_event, details='Before Alpine initializes'),
                CompletionItem('alpine:initialized', kind=kind_custom_event, details='After Alpine finishes initializing'),
            ]
            out = [c for c in lifecycle_events if c.trigger.lower().startswith(prefix.lower())]
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        # 1.5 CONTEXTO: Dentro del objeto raiz de Alpine.data(...)
        if self.is_inside_top_level_alpine_data_object(view, pt):
            lifecycle_methods = [
                CompletionItem.snippet_completion('init', 'init() {\n\t$1\n}', kind=kind_method, details='Alpine.data lifecycle method')
            ]
            out = [c for c in lifecycle_methods if c.trigger.lower().startswith(prefix.lower())]
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        # 2. CONTEXTO: Dentro de un VALOR de atributo
        attr_name, is_inside = self.get_current_alpine_attribute(view, pt)
        
        if is_inside:
            if attr_name:
                members = self.get_active_x_data_members(view, pt)
                store_definitions = self.get_registered_store_definitions(view)

                ignored_keys = {'get', 'set', 'return', 'if', 'else', 'this'}
                out = []

                store_member_match = re.search(r'\$store\.(\w+)\.(\w*)$', line_prefix)
                if store_member_match:
                    store_name, store_prefix = store_member_match.groups()
                    store_members = store_definitions.get(store_name, {})
                    for member_name in sorted(list(store_members)):
                        if member_name not in ignored_keys and member_name.lower().startswith(store_prefix.lower()):
                            member_kind = kind_method if store_members[member_name] == 'method' else kind_property
                            member_detail = 'Store Method' if store_members[member_name] == 'method' else 'Store Property'
                            out.append(CompletionItem(member_name, kind=member_kind, details=member_detail))
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                store_match = re.search(r'\$store\.(\w*)$', line_prefix)
                if store_match:
                    store_prefix = store_match.group(1).lower()
                    for store_name in sorted(list(self.get_registered_store_names(view))):
                        if store_name not in ignored_keys and store_name.lower().startswith(store_prefix):
                            out.append(CompletionItem(store_name, kind=kind_store, details='Registered Alpine.store'))
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                # Caso A: this.
                this_match = re.search(r'\bthis\.(\w*)$', line_prefix)
                if this_match:
                    this_prefix = this_match.group(1).lower()
                    for member_name in sorted(list(members)):
                        if member_name not in ignored_keys and member_name.lower().startswith(this_prefix):
                            member_kind = kind_method if members[member_name] == 'method' else kind_property
                            member_detail = 'Component Method' if members[member_name] == 'method' else 'Component Property'
                            out.append(CompletionItem(member_name, kind=member_kind, details=member_detail))
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                # Caso B: Variables normales
                iteration_vars = self.get_active_iteration_vars(view, pt)
                callback_vars = self.get_active_arrow_function_vars(view, pt)
                registered_data = self.get_registered_data_names(view) if attr_name == 'x-data' else set()
                completions = []
                
                for var in sorted(list(iteration_vars)):
                    if var not in ignored_keys:
                        completions.append(CompletionItem(var, kind=kind_variable, details='Iteration Variable'))

                for var in sorted(list(callback_vars)):
                    if var not in ignored_keys and var not in iteration_vars:
                        completions.append(CompletionItem(var, kind=kind_variable, details='Callback Variable'))

                for member_name in sorted(list(members)):
                    if member_name not in ignored_keys and member_name not in iteration_vars and member_name not in callback_vars:
                        member_kind = kind_method if members[member_name] == 'method' else kind_property
                        member_detail = 'Defined method in x-data' if members[member_name] == 'method' else 'Defined in x-data'
                        completions.append(CompletionItem(member_name, kind=member_kind, details=member_detail))

                for data_name in sorted(list(registered_data)):
                    if data_name not in ignored_keys:
                        completions.append(CompletionItem(data_name, kind=kind_data, details='Reusable Alpine.data'))
                
                magics = ['$event', '$dispatch', '$nextTick', '$refs', '$el', '$root', '$data', '$id', '$store']
                for magic in magics:
                    completions.append(CompletionItem(magic, kind=[KindId.SNIPPET, 'v', 'Magic Variable']))

                completions.append(
                    CompletionItem.snippet_completion(
                        '$watch',
                        r"\$watch('${1:property}', ${2:value} => ${3})",
                        kind=[KindId.SNIPPET, 'v', 'Magic Variable'],
                        details='Watch Alpine property changes'
                    )
                )

                out = [c for c in completions if c.trigger.lower().startswith(prefix.lower())]
                return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)
            else:
                return CompletionList([], flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        # 3. CONTEXTO: NOMBRE de atributo (Modificadores/Eventos)
        last_word = line_prefix.split()[-1] if line_prefix.strip() else ""
        if '.' in last_word:
            attr_base = last_word.split('.')[0]
            if attr_base.startswith('x-transition'):
                transition_values = []

                if re.search(r'x-transition(?::(?:enter|leave))?\.duration\.(\w*)$', last_word):
                    transition_values = [('75ms', '75 milliseconds'), ('150ms', '150 milliseconds'),
                                         ('300ms', '300 milliseconds'), ('500ms', '500 milliseconds')]
                elif re.search(r'x-transition(?::(?:enter|leave))?\.delay\.(\w*)$', last_word):
                    transition_values = [('50ms', '50 milliseconds'), ('75ms', '75 milliseconds'),
                                         ('150ms', '150 milliseconds'), ('300ms', '300 milliseconds')]
                elif re.search(r'x-transition(?::(?:enter|leave))?\.scale\.(\w*)$', last_word):
                    transition_values = [('75', 'Scale to 75%'), ('80', 'Scale to 80%'),
                                         ('90', 'Scale to 90%'), ('95', 'Scale to 95%')]
                elif re.search(r'x-transition(?::(?:enter|leave))?\.origin(?:\.[\w-]+)?\.(\w*)$', last_word):
                    transition_values = [('top', 'Top origin'), ('right', 'Right origin'),
                                         ('bottom', 'Bottom origin'), ('left', 'Left origin')]

                if transition_values:
                    out = [CompletionItem(value, kind=kind_modifier, details=desc) for value, desc in transition_values]
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                transition_modifiers = [('duration', 'Set transition duration'), ('delay', 'Set transition delay'),
                                        ('opacity', 'Opacity only transition'), ('scale', 'Scale only transition'),
                                        ('origin', 'Set scale origin'), ('top', 'Top origin'),
                                        ('right', 'Right origin'), ('bottom', 'Bottom origin'),
                                        ('left', 'Left origin')]
                out = [CompletionItem(mod, kind=kind_modifier, details=desc) for mod, desc in transition_modifiers]
                return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

            if attr_base.startswith(('@', 'x-on:')):
                event_name = re.sub(r'^(?:@|x-on:)', '', attr_base)
                line_suffix = view.substr(Region(pt, view.line(pt).b))
                has_assignment = bool(re.match(r'^\s*=', line_suffix))

                if re.search(r'(?:@|x-on:)[\w-]+(?:\.(?:window|document))?\.passive\.(\w*)$', last_word):
                    out = [CompletionItem('false', kind=kind_modifier, details='Make listener cancelable')]
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                if re.search(r'(?:@|x-on:)[\w-]+(?:\.[\w-]+)*\.(?:debounce|throttle)\.(\w*)$', last_word):
                    timings = [('75ms', '75 milliseconds'), ('150ms', '150 milliseconds'),
                               ('250ms', '250 milliseconds'), ('500ms', '500 milliseconds'),
                               ('750ms', '750 milliseconds'), ('1000ms', '1000 milliseconds')]
                    out = [CompletionItem(value, kind=kind_modifier, details=desc) for value, desc in timings]
                    return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

                generic_modifiers = [('prevent', 'preventDefault'), ('stop', 'stopPropagation'),
                                     ('outside', 'Outside element'), ('window', 'Listen on window'),
                                     ('document', 'Listen on document'), ('once', 'Only once'),
                                     ('debounce', 'Debounce handler'), ('throttle', 'Throttle handler'),
                                     ('self', 'Only self'), ('camel', 'Convert event name to camelCase'),
                                     ('dot', 'Convert dashes to dots in event name'),
                                     ('passive', 'Passive event listener'), ('capture', 'Capture phase listener')]
                keyboard_modifiers = [('shift', 'Shift key'), ('enter', 'Enter key'), ('space', 'Space key'),
                                      ('ctrl', 'Ctrl key'), ('cmd', 'Cmd key'), ('meta', 'Meta key'),
                                      ('alt', 'Alt key'), ('up', 'Arrow up'), ('down', 'Arrow down'),
                                      ('left', 'Arrow left'), ('right', 'Arrow right'),
                                      ('escape', 'Escape key'), ('tab', 'Tab key'),
                                      ('caps-lock', 'Caps Lock key'), ('equal', 'Equal key'),
                                      ('period', 'Period key'), ('comma', 'Comma key'),
                                      ('slash', 'Slash key'), ('page-down', 'Page Down key'),
                                      ('page-up', 'Page Up key'), ('home', 'Home key'),
                                      ('end', 'End key'), ('backspace', 'Backspace key'),
                                      ('delete', 'Delete key')]
                mouse_modifiers = [('shift', 'Shift key'), ('ctrl', 'Ctrl key'),
                                   ('cmd', 'Cmd key'), ('meta', 'Meta key'), ('alt', 'Alt key')]

                modifiers = list(generic_modifiers)
                if event_name in {'keydown', 'keyup', 'keypress'}:
                    modifiers = keyboard_modifiers + modifiers
                elif event_name in {
                    'click', 'auxclick', 'contextmenu', 'dblclick', 'mouseover', 'mousemove',
                    'mouseenter', 'mouseleave', 'mouseout', 'mouseup', 'mousedown'
                }:
                    modifiers = mouse_modifiers + modifiers

                out = [CompletionItem(mod, kind=kind_modifier, details=desc) if has_assignment else
                       CompletionItem.snippet_completion(mod, mod + '="$1"', kind=kind_modifier, details=desc)
                       for mod, desc in modifiers]
                return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        if re.search(r'(?:x-on:|@)[\w-]*$', line_prefix):
            descendant_custom_events = self.get_descendant_custom_event_names(view, pt)
            global_custom_events = self.get_dispatched_custom_event_names(view)
            events = [
                'click', 'submit', 'input', 'change', 'focus', 'blur', 'keydown', 'keyup',
                'keypress', 'mousedown', 'mouseup', 'mousemove', 'mouseenter', 'mouseleave',
                'mouseover', 'mouseout', 'contextmenu', 'dblclick', 'auxclick', 'scroll',
                'resize', 'touchstart', 'touchmove', 'touchend', 'pointerdown', 'pointerup',
                'pointermove', 'pointerenter', 'pointerleave', 'transitionend', 'animationend',
                'load', 'unload'
            ]
            line_suffix = view.substr(Region(pt, view.line(pt).b))
            has_assignment = bool(re.match(r'^\s*=', line_suffix))
            out = [CompletionItem(event, kind=kind_custom_event, details='Custom event dispatched in children') if has_assignment else
                   CompletionItem.snippet_completion(event, event + '="$1"', kind=kind_custom_event, details='Custom event dispatched in children')
                   for event in sorted(descendant_custom_events)]
            out.extend([
                CompletionItem(f'{event}.window', kind=kind_custom_event, details='Custom event dispatched outside current element')
                if has_assignment else
                CompletionItem.snippet_completion(f'{event}.window', f'{event}.window="$1"', kind=kind_custom_event, details='Custom event dispatched outside current element')
                for event in sorted(global_custom_events - descendant_custom_events)
            ])
            out.extend([
                CompletionItem(event, kind=kind_event) if has_assignment else
                CompletionItem.snippet_completion(event, event + '="$1"', kind=kind_event)
                for event in sorted(events) if event not in global_custom_events
            ])
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        if re.search(r'(?:x-bind:|:)[\w:-]*$', line_prefix):
            line_suffix = view.substr(Region(pt, view.line(pt).b))
            has_assignment = bool(re.match(r'^\s*=', line_suffix))
            bind_targets = [
                ('class', 'Bind CSS classes'),
                ('style', 'Bind inline styles'),
                ('placeholder', 'Bind placeholder text'),
                ('value', 'Bind input value'),
                ('type', 'Bind input type'),
                ('disabled', 'Bind disabled state'),
                ('checked', 'Bind checked state'),
                ('selected', 'Bind selected state'),
                ('readonly', 'Bind readonly state'),
                ('required', 'Bind required state'),
                ('hidden', 'Bind hidden state'),
                ('open', 'Bind open state'),
                ('id', 'Bind element id'),
                ('name', 'Bind form name'),
                ('for', 'Bind label target'),
                ('tabindex', 'Bind tab order'),
                ('role', 'Bind ARIA role'),
                ('href', 'Bind link destination'),
                ('src', 'Bind source URL'),
                ('alt', 'Bind alt text'),
                ('title', 'Bind title text'),
                ('aria-label', 'Bind accessible label'),
                ('aria-expanded', 'Bind expanded state'),
                ('aria-controls', 'Bind controlled element'),
                ('aria-hidden', 'Bind hidden state'),
            ]
            out = [CompletionItem(target, kind=kind_attribute, details=desc) if has_assignment else
                   CompletionItem.snippet_completion(target, target + '="$1"', kind=kind_attribute, details=desc)
                   for target, desc in bind_targets]
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        if re.search(r'x-transition:[\w-]*$', line_prefix):
            line_suffix = view.substr(Region(pt, view.line(pt).b))
            has_assignment = bool(re.match(r'^\s*=', line_suffix))
            phases = [('enter', 'Applied during the entering phase'),
                      ('enter-start', 'Before element is inserted'),
                      ('enter-end', 'After element is inserted'),
                      ('leave', 'Applied during the leaving phase'),
                      ('leave-start', 'When a leave transition starts'),
                      ('leave-end', 'After a leave transition starts')]
            out = [CompletionItem(phase, kind=kind_directive, details=desc) if has_assignment else
                   CompletionItem.snippet_completion(phase, phase + '="$1"', kind=kind_directive, details=desc)
                   for phase, desc in phases]
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)

        # 4. CONTEXTO: Directivas base x-* 
        if view.match_selector(pt, 'meta.tag'):
            attr_context = view.substr(Region(max(0, pt - 500), pt))
            tag_name_match = re.search(r'<(\w+)[^>]*$', attr_context)
            is_template = tag_name_match and tag_name_match.group(1).lower() == 'template'

            if is_template:
                out = [CompletionItem.snippet_completion('x-for', 'x-for="${1:item} in ${2:items}" :key="${3:$1}"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-if', 'x-if="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-teleport', 'x-teleport="$1"', kind=kind_directive)]
            else:
                out = [CompletionItem.snippet_completion('x-data', 'x-data="{ $1 }"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-init', 'x-init="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-show', 'x-show="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-bind', 'x-bind:$1="$2"', kind=kind_directive),
                       CompletionItem.snippet_completion(':class', ':class="$1"', kind=kind_attribute, details='Bind CSS classes'),
                       CompletionItem.snippet_completion(':style', ':style="$1"', kind=kind_attribute, details='Bind inline styles'),
                       CompletionItem.snippet_completion(':disabled', ':disabled="$1"', kind=kind_attribute, details='Bind disabled state'),
                       CompletionItem.snippet_completion(':placeholder', ':placeholder="$1"', kind=kind_attribute, details='Bind placeholder text'),
                       CompletionItem.snippet_completion('x-on', 'x-on:$1="$2"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-text', 'x-text="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-html', 'x-html="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-model', 'x-model="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-modelable', 'x-modelable="$1"', kind=kind_directive),
                       CompletionItem.snippet_completion('x-transition', 'x-transition', kind=kind_directive, details='Transition helper'),
                       CompletionItem.snippet_completion('x-transition:enter', 'x-transition:enter="$1"', kind=kind_directive, details='Enter transition classes'),
                       CompletionItem.snippet_completion('x-transition:enter-start', 'x-transition:enter-start="$1"', kind=kind_directive, details='Enter start classes'),
                       CompletionItem.snippet_completion('x-transition:enter-end', 'x-transition:enter-end="$1"', kind=kind_directive, details='Enter end classes'),
                       CompletionItem.snippet_completion('x-transition:leave', 'x-transition:leave="$1"', kind=kind_directive, details='Leave transition classes'),
                       CompletionItem.snippet_completion('x-transition:leave-start', 'x-transition:leave-start="$1"', kind=kind_directive, details='Leave start classes'),
                       CompletionItem.snippet_completion('x-transition:leave-end', 'x-transition:leave-end="$1"', kind=kind_directive, details='Leave end classes'),
                       CompletionItem.snippet_completion('x-effect', 'x-effect="$1"', kind=kind_directive),
                       CompletionItem('x-ignore', kind=kind_directive),
                       CompletionItem.snippet_completion('x-ref', 'x-ref="$1"', kind=kind_directive),
                       CompletionItem('x-cloak', kind=kind_directive),
                       CompletionItem.snippet_completion('x-id', 'x-id="$1"', kind=kind_directive)]
            return CompletionList(out, flags=AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS)
            
        return CompletionList([])
