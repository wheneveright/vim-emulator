# 基于 Pygame 的 Vim 模拟编辑器

这是一个使用 Python 和 Pygame 开发的轻量级 Vim 模拟编辑器，旨在还原 Vim 的核心功能，包括模式编辑、可配置的按键绑定以及基本的文本操作。通过这个项目，用户可以深入理解 Vim 的设计逻辑，并根据需求对编辑器的行为进行自由调整。


## 项目背景

Vim 是一款非常强大的文本编辑器，以其模式化的操作和高度的可扩展性闻名。出于对 Vim 核心功能的兴趣，我决定用 Python 和 Pygame 来实现一个简化版的 Vim 编辑器。  
在开发过程中，我从第一人称视角思考如何将 Vim 的设计理念与 Python 的灵活性结合，实现一个适合学习与实验的编辑器，同时通过易懂的代码架构让用户可以轻松定制和扩展。

这个项目的实现过程帮助我深入理解了以下几个方面：
1. 模式化编辑的操作逻辑和事件处理机制。
2. 如何通过配置文件让功能更加灵活且可定制。
3. 文本编辑器在性能和易用性之间的平衡点。


## 项目功能

### 核心特性

- **多模式编辑**:
  - `NORMAL` 模式：执行文本导航和命令操作。
  - `INSERT` 模式：直接插入文本。
  - `COMMAND` 模式：输入并执行命令（如保存、退出等）。
	<!-- - `VISUAL` 模式：只做了最基本的高亮，还处于开发状态 -->
	<!-- TODO: 还有很重要的 `SEARCH` 模式没有实现 -->

- **可配置的按键绑定**：用户可以通过 TOML 配置文件灵活调整按键功能。

- **基本文本操作**：
  - 插入、删除和移动文本。
  - 行操作（如合并、删除、上下插入新行）。
  - 单词级别的精确导航（如 `w`、`b`、`e`）。

- **数字前缀支持**：允许用户在 NORMAL 模式下指定操作的重复次数。例如：
  - 3w：将光标向前移动 3 个单词。
  - 5x：连续删除 5 个字符。
  - 10o：在当前行下插入 10 行新行。

- **文件操作**：支持文件加载和保存。

- **轻量化架构**：代码易于扩展和维护。

## 使用指南

### 环境准备

在开始使用之前，请确保已安装以下软件：

- **Python 3.11+**
- **Pygame**：可以通过以下命令安装：  
  **windows**:
  ```bash
  pip install pygame
  ```
  **linux**:
  ```bash
  sudo apt install python3-pygame
  ```

<!-- TODO: 上传到 github 上 -->
<!-- ### 获取项目代码 -->
<!---->
<!-- ```bash -->
<!-- git clone https://github.com/0WD0/vim-emulator.git -->
<!-- cd vim-emulator -->
<!-- ``` -->

### 运行编辑器

```bash
python main.py
```

## 按键绑定

默认按键绑定参考了 Vim 的基本操作，用户可以通过编辑 `config.toml` 文件自定义按键映射。
配置中设置的函数名是应该是直接可读的，如果有疑问可以自行测试或查询 Vim 文档，理想情况下它们的行为应该和它们在 Vim 中的行为一致。

## 配置文件

以下是默认按键绑定：

```toml
[keybindings.NORMAL]
h = "move_cursor_left"
l = "move_cursor_right"
j = "move_cursor_down"
k = "move_cursor_up"
i = "switch_to_insert"
I = ['^','i']
x = ["a","backspace","escape"]
':' = "switch_to_command"
q = "quit"
o = "new_line"
O = "new_line_upward"
'^' = "line_begin"
'$' = "line_end"
a = 'append_char'
s = ['x','i']
A = ['$','a']
w = "next_word"
W = "next_WORD"
D = "delete_line"
S = ['D','i']
J = "join_next_line"
escape = "clean_oplist"
b = "last_word"
B = "last_WORD"
e = "next_word_end"
E = "next_WORD_end"
f = "inline_search"
F = "inline_search_backward"
t = "inline_search_until"
T = "inline_search_backward_until"
r = "replace_char"


[keybindings.INSERT]
escape = "switch_to_normal"
return = "split_line"
backspace = "delete_char"

[keybindings.COMMAND]
return = "execute_command"
backspace = "delete_command"
escape = "switch_to_normal"
```

用户可以自由修改此文件以调整按键行为或添加新功能。


## 功能细节

### 多模式编辑

1. **NORMAL 模式**：主要用于文本导航（如 `h`、`j`、`k`、`l`）、删除操作（如 `x`、`D`）或创建新行（如 `o`、`O`）。
2. **INSERT 模式**：通过 `i` 或 `a` 进入，用于直接插入文本。
3. **COMMAND 模式**：通过 `:` 进入，用于执行诸如 `:w`（保存文件）或 `:q`（退出）的命令。

#### 命令模式
这个模式需要额外说明，我们可以通过 `:functionName arg1 arg2 ... <CR>` 这样的方式执行 VimEmulator 类中的定义的函数
也可以同时放多组函数及其对应参数在其中，程序可以自己识别读入的函数需要几个参数

### 文本操作

- **光标导航**：支持字符级别、单词级别、行首与行尾的精确定位。
- **行操作**：通过 `J` 合并行，使用 `D` 删除整行。
- **文件操作**：通过 COMMAND 模式加载或保存文件。

### 文件操作

并没有实现太多功能，实现了最最基本的保存话加载功能

- **save_to_file**: 保存缓冲区到文件
- **load_from_file**: 从文件加载缓冲区

### 自定义按键绑定

编辑器支持通过 TOML 文件配置按键映射，允许用户：
- 重新定义按键功能。
- 配置复杂的组合操作序列。


## 未来计划

- 添加语法高亮功能。
- 实现撤销与重做功能。
- 优化大文件的渲染性能。
- 支持多文件编辑。
- 增强测试覆盖率，支持更多边缘情况。
- 提供打包好的可执行文件，方便分发。


## 许可证

本项目基于 MIT 许可证发布，详细信息请参阅 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎任何形式的贡献！如果您发现问题或有改进建议，请随时提交 Issue 或 Pull Request。
