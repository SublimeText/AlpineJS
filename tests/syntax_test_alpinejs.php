-- SYNTAX TEST "PHP (AlpineJS).sublime-syntax"

<!--
 Directives
 -->

<div x-data="{ open: {{ $var }} }"></div>
--   ^^^^^^^ meta.tag meta.attribute-with-value.alpinejs.html - meta.string
--          ^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html - meta.interpolation
--           ^^^^^^^^^^^^^^^^^^^^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html meta.interpolation.html
--                               ^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html - meta.interpolation
--   ^^^^^^ entity.other.attribute-name.alpinejs.html
--         ^ punctuation.separator.key-value.html
--          ^ string.quoted.double.html punctuation.definition.string.begin.html
--           ^^^^^^^^^^^^^^^^^^^^ source.js.embedded.html meta.block.js - string
--           ^ punctuation.section.block.begin.js
--             ^^^^ entity.name.label.js
--                 ^ punctuation.separator.js
--                   ^^ punctuation.section.block.begin.js
--                      ^^^^ variable.other.dollar.js
--                           ^^ punctuation.section.block.end.js
--                              ^ punctuation.section.block.end.js
--                                ^ punctuation.definition.tag.end.html

<div x-init="console.log('I\'m being <?php echo 'initialized!'; ?>')"></div>
--   ^^^^^^^ meta.tag meta.attribute-with-value.alpinejs.html - meta.string
--          ^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html string.quoted.double.html punctuation.definition.string.begin.html
--           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html meta.interpolation.html source.js.embedded.html
--                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.function-call meta.group.js meta.string.js meta.embedded.php
--                                                                  ^ meta.tag meta.attribute-with-value.alpinejs.html meta.string.html string.quoted.double.html punctuation.definition.string.end.html

<div x-show="open">Dropdown Contents...</div>
--   ^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--   ^^^^^^ entity.other.attribute-name.alpinejs.html
--         ^ punctuation.separator.key-value.html
--          ^^^^^^ meta.string.html
--          ^ string.quoted.double.html punctuation.definition.string.begin.html
--           ^^^^ source.js.embedded.html variable.other.readwrite.js
--               ^ string.quoted.double.html punctuation.definition.string.end.html

<input type="text" x-bind:placeholder="placeholder">
--                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--                 ^^^^^^^^^^^^^^^^^^ entity.other.attribute-name.alpinejs.html
--                                   ^ punctuation.separator.key-value.html
--                                    ^^^^^^^^^^^^^ meta.string.html
--                                    ^ string.quoted.double.html punctuation.definition.string.begin.html
--                                     ^^^^^^^^^^^ source.js.embedded.html variable.other.readwrite.js
--                                                ^ string.quoted.double.html punctuation.definition.string.end.html

<input type="text" :placeholder="placeholder">
--                 ^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--                 ^^^^^^^^^^^^ entity.other.attribute-name.alpinejs.html
--                             ^ punctuation.separator.key-value.html
--                              ^^^^^^^^^^^^^ meta.string.html
--                              ^ string.quoted.double.html punctuation.definition.string.begin.html
--                               ^^^^^^^^^^^ source.js.embedded.html variable.other.readwrite.js
--                                          ^ string.quoted.double.html punctuation.definition.string.end.html

<button x-on:click="alert('Hello World!')">Say Hi</button>
--      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--      ^^^^^^^^^^ entity.other.attribute-name.alpinejs.html
--                ^ punctuation.separator.key-value.html
--                 ^^^^^^^^^^^^^^^^^^^^^^^ meta.string.html
--                 ^ string.quoted.double.html punctuation.definition.string.begin.html
--                  ^^^^^^^^^^^^^^^^^^^^^ source.js.embedded.html meta.function-call
--                                       ^ string.quoted.double.html punctuation.definition.string.end.html

<button x-on:click.prevent="alert('Hello World!')">Say Hi</button>
--      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--      ^^^^^^^^^^^^^^^^^^ entity.other.attribute-name.alpinejs.html
--                        ^ punctuation.separator.key-value.html
--                         ^^^^^^^^^^^^^^^^^^^^^^^ meta.string.html
--                         ^ string.quoted.double.html punctuation.definition.string.begin.html
--                          ^^^^^^^^^^^^^^^^^^^^^ source.js.embedded.html meta.function-call
--                                               ^ string.quoted.double.html punctuation.definition.string.end.html

<button @click="alert('Hello World!')">Say Hi</button>
--      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
--      ^^^^^^ entity.other.attribute-name.alpinejs.html
--            ^ punctuation.separator.key-value.html
--             ^^^^^^^^^^^^^^^^^^^^^^^ meta.string.html
--             ^ string.quoted.double.html punctuation.definition.string.begin.html
--              ^^^^^^^^^^^^^^^^^^^^^ source.js.embedded.html meta.function-call
--                                   ^ string.quoted.double.html punctuation.definition.string.end.html

<div x-data="{ username: 'calebporzio' }">
    Username: <strong x-text="username"></strong>
    --                ^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
    --                ^^^^^^ entity.other.attribute-name.alpinejs.html
    --                      ^ punctuation.separator.key-value.html
    --                       ^ meta.string.html string.quoted.double.html punctuation.definition.string.begin.html
    --                        ^^^^^^^^ meta.string.html source.js.embedded.html variable.other.readwrite.js
    --                                ^ meta.string.html string.quoted.double.html punctuation.definition.string.end.html
</div>

<div x-data="{ username: '<strong>calebporzio</strong>' }">
    Username: <span x-html="username"></span>
    --              ^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
    --              ^^^^^^ entity.other.attribute-name.alpinejs.html
    --                    ^ punctuation.separator.key-value.html
    --                     ^ meta.string.html string.quoted.double.html punctuation.definition.string.begin.html
    --                      ^^^^^^^^ meta.string.html source.js.embedded.html variable.other.readwrite.js
    --                              ^ meta.string.html string.quoted.double.html punctuation.definition.string.end.html
</div>

<div x-data='{ username: "<strong>calebporzio</strong>" }'>
    --      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html meta.string.html
    --      ^ string.quoted.single.html punctuation.definition.string.begin.html
    --       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.js.embedded.html meta.block.js - string.quoted.single
    --                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.string.js string.quoted.double.js
    --                                                   ^ string.quoted.single.html punctuation.definition.string.end.html

    Username: <span x-html='username'></span>
    --              ^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
    --              ^^^^^^ entity.other.attribute-name.alpinejs.html
    --                    ^ punctuation.separator.key-value.html
    --                     ^ meta.string.html string.quoted.single.html punctuation.definition.string.begin.html
    --                      ^^^^^^^^ meta.string.html source.js.embedded.html variable.other.readwrite.js
    --                              ^ meta.string.html string.quoted.single.html punctuation.definition.string.end.html
</div>

<div x-data="{ message: '' }">
    <input type="text" x-model="message">
    --                 ^^^^^^^^^^^^^^^^^ meta.attribute-with-value.alpinejs.html
    --                 ^^^^^^^ entity.other.attribute-name.alpinejs.html
    --                        ^ punctuation.separator.key-value.html
    --                         ^ meta.string.html string.quoted.double.html punctuation.definition.string.begin.html
    --                          ^^^^^^^ meta.string.html source.js.embedded.html variable.other.readwrite.js
    --                                 ^ meta.string.html string.quoted.double.html punctuation.definition.string.end.html
</div>


<!--
 Events
 -->
