# Lv9+.1. 你的编译器超强的

> “除了用来交作业, 我的编译器到底还能做什么?”

可能很多同学在完成编译实践之后, 都会有这样的疑问.

确实, 同学们实现的编译器看上去只能处理一些简单的不能再简单的程序. 你可以打开之前用来测试编译器的[测试用例仓库](https://github.com/pku-minic/compiler-dev-test-cases)看一眼, 里面都是一些破碎不堪的程序 (毕竟只是为了罗列并测试相关功能), 和一些完全不知所云的把 CPU 当狗遛的程序 (分支, 循环和函数的组合能测出编译器的很多 bug). 其中最复杂的程序, 只是几个排序算法的实现而已.

难道你写的编译器只能用来编译一些排序算法吗?

**当然不是, 你的编译器超强的!**

## SysY 是图灵完备的

在编程语言的语境下, 图灵完备 ([Turing-complete](https://en.wikipedia.org/wiki/Turing_completeness)) 指的是, 某种编程语言可以用来模拟任何一种图灵机 ([Turing machine](https://en.wikipedia.org/wiki/Turing_machine)), 图灵机能做什么事情, 这种编程语言也可以做同样的事情. 如果某种编程语言是图灵完备的, 那它也可以用来模拟其他图灵完备的系统.

为什么说 SysY 是图灵完备的呢? 它具备各种控制流语句, 可以用来表达任何形式分支和循环; 同时它可以定义变量或者数组变量, 于是用它编写的程序可以存取各类数据. 虽然我们没有形式化地证明 SysY 是图灵完备的, 但我们不难看出, 具备上述能力之后, SysY 足以模拟一个具备纸带和读写头的图灵机.

抛开那些严谨的定义, 我们通常说某种编程语言是图灵完备的, 指的是我们可以用这种编程语言模拟任何其他的, 通常意义上的计算机系统. SysY 是图灵完备的, 所以 SysY 完全可以模拟任何现实世界中的计算机系统, 或者实现任何计算机程序. 比如你可以用 SysY 实现一个 x86-64 的软件虚拟机, 然后在上面运行 Windows 11, 再跑一个 SysY 写的坎巴拉太空计划或者 Minecraft 之类的——当然, 性能高不高另说.

你的编译器可以把任何 SysY 程序编译到 RISC-V 汇编, 于是, 你的编译器足以编译并生成任何复杂的程序.

## 一些有趣的例子

不要被 SysY 简单的外表所欺骗, 也别被 SysY 限制了想象力. 有的时候, 你只需要稍微花点时间, 就能用 SysY 写出很多有趣的东西.

为了让你认识到, 你写的编译器真的很强, 我们特地写了一些比较有趣的 SysY 程序, 详情请见 GitHub 上的 [awesome-sysy](https://github.com/pku-minic/awesome-sysy) 仓库.

这其中, 有些程序完全符合 SysY 的语法定义, 也就是说, **只要你正确实现了你的编译器, 你就可以尝试把这些程序编译到 Koopa IR 或者 RISC-V, 然后运行它们, 试玩一下.** 另一些程序使用了一些不属于 SysY 的扩展语法, 你的编译器还需要支持一些额外的 C 语言语法, 才能处理这些程序. (当然, 并不是说不扩展语法这些程序就写不出来, 只是说, 纯用 SysY 写这些程序实在太费劲了, ~助教懒得搞了~)

### maze

[maze](https://github.com/pku-minic/awesome-sysy/tree/master/maze) 程序就是用纯 SysY 实现的, 它可以随机生成一个 $100 \times 100$ 的迷宫, 然后把生成结果输出到图像:

![生成的迷宫](maze.png)

### mandelbrot

[mandelbrot](https://github.com/pku-minic/awesome-sysy/blob/master/mandelbrot) 程序可以绘制 [Mandelbrot 集](https://en.wikipedia.org/wiki/Mandelbrot_set), 并且把绘制的结果输出到图像中. 这个程序要求你的 SysY 编译器支持函数声明的语法:

```ebnf
FuncDecl ::= FuncType IDENT "(" [FuncFParams] ")";
```

其语义和 C 语言中的函数声明类似. 程序输出的图像如下:

![Mandelbrot](mandelbrot.png)

~太潮辣!~ 是不是很漂亮?

### lisp

[lisp](https://github.com/pku-minic/awesome-sysy/tree/master/lisp) 程序**用纯 SysY 实现了一个带[引用计数 GC](https://en.wikipedia.org/wiki/Reference_counting) 的 Lisp 解释器.** 你的编译器不需要支持任何额外特性, 就可以编译这个程序.

这个解释器所支持的 [Lisp 语言](https://en.wikipedia.org/wiki/Lisp_(programming_language))也是一种图灵完备的编程语言, 如果你读过/学过 [SICP](https://en.wikipedia.org/wiki/Structure_and_Interpretation_of_Computer_Programs) 的话, 你对 Lisp 应该并不陌生. 比如你可以用解释器执行一些 Lisp 程序:

```bash
# 使用你的编译器编译 lisp.c, 然后把结果生成成可执行文件
# ...

# 向 input.lisp 文件里写入一些 Lisp 代码
cat > input.lisp <<EOF
(define fib
  (lambda (n)
    (cond ((<= n 2) 1)
          ('t (+ (fib (- n 1)) (fib (- n 2)))))))
(fib 20)
EOF
# 使用 lisp 程序解释执行 input.lisp 里的程序
./lisp < input.lisp
```

你可以看到程序输出了 `6765`, 也就是[斐波那契数列](https://en.wikipedia.org/wiki/Fibonacci_number#Definition)第 20 项的值.

当然, Lisp 也分相当多种, 至于 `lisp` 程序具体支持哪些操作, 你可以 RTFSC.

此外, 我们还随 `lisp.c` 附赠了一个 [`lisp.lisp` 文件](https://github.com/pku-minic/awesome-sysy/blob/master/lisp/lisp.lisp). 你可能已经猜到了, 这是一个使用 Lisp 实现的 Lisp 解释器, 更神奇的是, 你的编译器生成的 `lisp` 程序也可以运行这个简单的解释器:

```bash
./lisp < lisp.lisp
# 输出:
# by-MaxXing
# Reference:-Roots-of-Lisp
# (1 1 2 3 5 8 13 21 34 55)
```

也就是说, 你在编译实践课上实现了一个编译器, 这个编译器可以编译一个解释器, 然后编译得到的解释器又可以解释执行另一个解释器, 这个解释器会解释执行一个输出斐波那契数列的程序——所以, 如果你还没被套娃绕晕的话, 相信我, **你的编译器超强的!** 上完编译课之后, 你就可以拍着胸脯和其他同学说:

> “我在编译课上, 用自己写的编译器, 编译了一个可以用来做函数式程序设计课作业的程序.”

感兴趣的话, 你可以读一读 `lisp.lisp` 的代码, 然后感受一下, (Lisp (是一种 (多么) (简洁的 (编程语言)))).

## 实现更有趣的程序

你也许会觉得, 上面的示例程序也不够有趣, 你想自己实现一些更有趣的 SysY 程序, 比如小工具, 小游戏, [demoscene](https://en.wikipedia.org/wiki/Demoscene), 甚至操作系统. 或者, 你觉得你的编译器支持的语法不够炫酷, 你希望给它添加一些更强大的特性, 无论是符合 C 语言风格的特性 (函数声明, 指针, 结构体等), 还是天马行空的特性 (匿名函数, 宏, 泛型等).

我们欢迎任何形式的, 能让你的编译器看起来更有趣的工作. 如果你实现了这些工作, 你可以把它们写进最终的实验报告, 我们会视情况加分.

?> **TODO:** 评分细则待补充.

此外, 如果你写了一些比较炫酷的 SysY 程序, 欢迎向 [awesome-sysy](https://github.com/pku-minic/awesome-sysy) 仓库发起 pull request. 也许下一届的学弟学妹们在用他们写的编译器编译你的程序的时候, 也能从中体验到满满的成就感.
