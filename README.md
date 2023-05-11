AlpineJS
========

[AlpineJS](https://alpinejs.dev) syntax definitions for [Sublime Text](https://www.sublimetext.com) based on its HTML and PHP syntaxes.

## Installation

### Package Control

The easiest way to install is using [Package Control](https://packagecontrol.io). It's listed as `AlpineJS`.

1. Open `Command Palette` using <kbd>ctrl+shift+P</kbd> or menu item `Tools → Command Palette...`
2. Choose `Package Control: Install Package`
3. Find `AlpineJS` and hit <kbd>Enter</kbd>

### Manual Install

1. Download appropriate [AlpineJS.sublime-package](https://github.com/SublimeText/AlpineJS/releases) for your Sublime Text build.
2. Rename it to _AlpineJS.sublime-package_
3. Copy it into _Installed Packages_ directory
   
> To find _Installed Packages_...
>
> 1. call _Menu > Preferences > Browse Packages.._
> 2. Navigate to parent folder

## Requirements

- requires Sublime Text 4143+

## Astro

AlpineJS can be combined with [Astro](https://packagecontrol.io/packages/Astro).

Just create a _HTML (Astro, AlpineJS).sublime-syntax_ with following content in your _User_ package.

```yaml
%YAML 1.2
---
# http://www.sublimetext.com/docs/syntax.html
name: HTML (Astro, AlpineJS)
scope: text.html.Astro.alpinejs
version: 2

extends:
  - Packages/AlpineJS/Syntaxes/HTML (AlpineJS).sublime-syntax
  - Packages/Astro/Syntaxes/HTML (Astro).sublime-syntax
```

## Laravel Blade

AlpineJS can be combined with [Laravel Blade Highlighter v2.0.0+](https://packagecontrol.io/packages/Laravel%20Blade%20Highlighter).

Just create a _HTML (Blade, AlpineJS).sublime-syntax_ with following content in your _User_ package.

```yaml
%YAML 1.2
---
# http://www.sublimetext.com/docs/syntax.html
name: HTML (Blade, AlpineJS)
scope: text.html.blade.alpinejs
version: 2

extends:
  - Packages/AlpineJS/Syntaxes/PHP (AlpineJS).sublime-syntax
  - Packages/Laravel Blade Highlighter/Syntaxes/HTML (Blade).sublime-syntax
```

## Elixir HEEx

AlpineJS can be combined with [ElixirSyntax](https://packagecontrol.io/packages/ElixirSyntax).

Just create a _HTML (HEEx, AlpineJS).sublime-syntax_ with following content in your _User_ package.

```yaml
%YAML 1.2
---
# http://www.sublimetext.com/docs/syntax.html
name: HTML (HEEx, AlpineJS)
scope: text.html.heex.alpinejs
version: 2

extends:
  - Packages/AlpineJS/Syntaxes/HTML (AlpineJS).sublime-syntax
  - Packages/ElixirSyntax/syntaxes/HTML (HEEx).sublime-syntax
```
