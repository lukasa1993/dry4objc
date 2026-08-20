# dry4objc

`dry4objc` finds duplicated normalized token windows in Objective-C and Objective-C++ source.

## Install

```bash
pipx install git+https://github.com/lukasa1993/dry4objc.git
```

## Run

```bash
dry4objc --min-tokens 40 --fail
```

Comments and whitespace are ignored. Identifiers, string literals, and numbers are normalized, so structurally duplicated blocks can be found after local renaming.
