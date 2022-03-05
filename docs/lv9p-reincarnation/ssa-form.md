# Lv9+.4. SSA 形式

SSA 形式是 IR 可以具备的一种特性, 它的英文全称是 [Static Single Assignment form](https://en.wikipedia.org/wiki/Static_single_assignment_form), 即静态单赋值形式. Koopa IR 正是一种 SSA 形式的 IR.

在前几章的学习中, 你已经知道, Koopa IR 要求 “所有的变量只能在定义的时候被赋值一次”. 也就是说, Koopa IR 中某个符号对应的变量, 它所代表的值并不会在程序执行的过程中被突然修改. 如果你想要达到 “修改” 的效果, 你必须使用 `alloc`/`load`/`store` 指令.

但实际上, 使用 `alloc`, `load` 和 `store` 只是一种妥协, 它们并不是 “原教旨主义” 的 SSA 形式. 这么妥协的原因是, 直接让编译器前端生成 SSA 形式的 IR 是比较复杂的, 我们也不希望在课程实践中引入复杂且难以理解的内容. 而这种基于 `alloc`/`load`/`store` 的表示则要好处理得多, 虽然它只是进入 SSA 形式前的一种过渡形式, 但你:

* 进可在此基础上把 Koopa IR 提升到 SSA 形式. 很多业界的编译器, 比如 LLVM, [就是这么做的](https://github.com/llvm/llvm-project/blob/main/llvm/lib/Transforms/Utils/PromoteMemoryToRegister.cpp).
* 退可就这么将就着用, 这种形式的 Koopa IR 对编译课来说完全够用.

## SSA 形式初见

说了这么多, SSA 形式的 IR 应该长什么样? 我们先不讨论 Koopa IR, 只基于 SSA 的定义来看一下, 比如对于下面这段 SysY 程序:

```c
int a = 1;
int b = 2;
a = a + b;
return a;
```

要怎么把它变成 SSA 形式的呢? 我们可以这么写:

```
a = 1       // 定义 a
b = 2       // 定义 b
a' = a + b  // a 已经被定义过了, 所以我们得换个名字
return a'   // 这里实际上使用的是 a' 的值
```

这里的 `a'` 就体现了 “单赋值” 的思想: `a'` 的定义顶替了 `a` 的定义, 因为我们试图修改 `a` 的值. 之后的 `return` 又会用到 `a`, 它用到的应该是最新的 `a`, 所以在 SSA 形式下, 它应该使用 `a'`.

相比大家印象中的变量, SSA 形式中的 “变量” 似乎并不应该叫变量, 因为它看起来根本不可变. 要想修改变量, 你就只能定义一个新的变量来顶替之前的那个. SSA 形式正是借助 “单赋值” 的思想, 简化了 “变量” 的特性, 最终使得程序变得比之前好分析得多. 比如你在 SysY 里写了这样一段代码:

```c
int a = 1;
a = 2;
return a;
```

之前给 `a` 的初始值 1 其实根本就没用, 因为紧接着 `a` 就被改成 2 了. 所以, 对应的给 `a` 写 1 的那个操作也就成了一个冗余操作. 如果变量可以被任意修改, 那这件事情并不好用程序来分析: 你可以想象一下在这段程序上做 [DCE](/lv9p-reincarnation/opt?id=死代码消除), 编译器其实一条指令都删不掉——当然这也是因为我们介绍的 DCE 在实现上没考虑得这么复杂, 基本是个 “青春版”. 但在 SSA 形式下, 这段代码就会变成:

```
a = 1
a' = 2
return a'
```

`a` 直接被架空了, `return` 只用了 `a'` 的值, 和 `a` 一点关系都没有. 如果此时我们做一次 DCE (青春版), 开头的那个 `a = 1` 很容易就被删除了. 从这一点, 你应该也能大致体会到 SSA 形式所带来的优势.

不过聪明的你可能会想到另一种情况:

```c
int a = 1;
if (...) {
  a = 2;
} else {
  a = 3;
}
return a;
```

这个程序要怎么翻译成 SSA 形式呢? 你也许可以试着做一下:

```
  a = 1               // 定义最初的 a
  br ..., then, else  // 执行条件判断

then:
  a_1 = 2     // 修改了 a 的值, 定义新变量 a_1
  jump end

else:
  a_2 = 3     // 修改了 a 的值, 定义新变量 a_2
  jump end

end:
  return ???  // 等等, 这里应该用哪个 a?
```

你会发现, 遇到这种控制流合并的情况, 一旦你在之前的两个控制流里对同一个变量做了不同的修改, 或者只在一个控制流里改了变量而另一个没改, 在控制流的交汇处再想用这个变量, 你就不知道到底该用哪一个了. 而 SSA 形式用一种近乎耍赖皮的方式解决了这个问题:

```
  a = 1
  br ..., then, else

then:
  a_1 = 2     // 修改了 a 的值, 定义新变量 a_1
  jump end

else:
  a_2 = 3     // 修改了 a 的值, 定义新变量 a_2
  jump end

end:
  // 定义一个新变量 a_3
  // 如果控制流是从 then 基本块流入的, 那 a_3 的值就是 a_1
  // 如果控制流是从 else 基本块流入的, 那 a_3 的值就是 a_2
  a_3 = phi (a_1, then), (a_2, else)
  return a_3  // 这里用 a_3
```

SSA “单赋值” 的特性一点也没受影响, 我们照样写出了正确的程序——只不过程序里多了个叫 `phi` 的奇怪玩意. `phi` 的学名叫做 $\phi$ 函数 ($\phi$ function) 或者 $\phi$ 节点 ($\phi$ node), 它存在的目的就是为了调和我们遇到的这种矛盾. 有了 $\phi$ 函数, 我们就可以在任何控制流下表示 SSA 形式了.

## SSA 形式的 Koopa IR

对于如下的 Koopa IR 程序:

```koopa
@a = alloc i32
store 1, @a

@b = alloc i32
store 2, @b

%0 = load @a
%1 = load @b
%2 = add %0, %1
store %2, @a

%ans = load @a
ret %ans
```

如果让你把 `alloc`/`load`/`store` 删掉, 并且维持单赋值的特性, 直觉上, 你可能会把它改成这个样子:

```koopa
@a = 1
@b = 2
%0 = @a
%1 = @b
%2 = add %0, %1
@a_1 = %2       // @a 已经被定义过一次了, 所以必须改个名字
%ans = @a_1
ret %ans
```

很好理解对吧, 这段程序已经和之前我们介绍的的 SSA 形式相差无几了. 不过 Koopa IR 有个要求: 指令列表里永远不会出现类似 `@符号 = 值` 的这种赋值指令, 并且 Koopa IR 的[规范](/misc-app-ref/koopa)中也没有定义这种表示赋值的指令. 实际的 Koopa IR 长这样:

```koopa
%2 = add 1, 2
ret %2
```

只有两条指令吗? 是的, 把所有的赋值都删掉之后, 程序里确实只剩下两条指令了, 我相信这个结果并不难理解, 这就是 SSA 形式的 Koopa IR.

另一件事情是, Koopa IR 没有支持 $\phi$ 函数, 而是采用了另一种等价的表示方法: 基本块参数 (basic block arguments). 比如对于之前举例的那段 SSA 程序:

```
  a = 1
  br ..., then, else

then:
  a_1 = 2
  jump end

else:
  a_2 = 3
  jump end

end:
  a_3 = phi (a_1, then), (a_2, else)
  return a_3
```

在 Koopa IR 中应该这样表示:

```koopa
  br ..., %then, %else

%then:
  jump %end(2)

%else:
  jump %end(3)

%end(%a_3: i32):
  ret %a_3
```

基本块参数就像函数参数一样, 相信对于你来说, 这并不难理解. 同时, 在 $\phi$ 函数和基本块参数这两种风格之间转换, 也是比较 trivial 的, 此处不再赘述. 至于为什么采用这样的设计, 你可以参考 MaxXing 写的某篇 blog: [SSA 形式的设计取舍: Phi 函数的新形式?](http://blog.maxxsoft.net/index.php/archives/143/).

## 进入和退出 SSA 形式

非 SSA 形式的 IR 要怎么转换到 SSA 形式呢? 看了之前的介绍, 你应该能大致感觉到: 把对变量的每一次修改都变成一次新定义看起来并不复杂, 复杂的是, 应该在哪些地方插入 $\phi$ 函数 (或者基本块参数).

另一方面, 由于在现实世界的指令系统里并不能找到和 $\phi$ 函数对应的指令, 我们通常需要在进行寄存器分配前后, 让 IR 退出 SSA 形式, 也就是把所有的 $\phi$ 函数都删掉, 转换成 ISA 中定义的寄存器或者内存. 所以, 你也需要理解退出 SSA 形式的方法.

关于进入和退出 SSA 形式的算法实现, 你可以参考 *Static Single Assignment Book*——没错, 有一群人专门给 SSA 形式写了本书, 其中总结了和 SSA 相关的种种, 包括基本介绍, 基于 SSA 的分析, SSA 形式的扩展, 面向 SSA 的机器代码生成, 等等, 可谓十分详尽.

SSA Book 的仓库最初被托管在 [Inria Forge](https://gforge.inria.fr/projects/ssabook/) 上, 但 2020 年这个网站关站了, 后来有人在 GitHub 上建立了[镜像仓库](https://github.com/pfalcon/ssabook). 目前的最新消息是, SSA Book 已经转生成了另一本书: *SSA-based Compiler Design*, 并且[已经出版](https://link.springer.com/book/9783030805142).

关于进入 SSA 形式的实现, 你还可以参考论文: [*Cytron et al. 1991, "Efficiently computing static single assignment form and the control dependence graph"*](https://doi.org/10.1145%2F115372.115320), 其中介绍的算法是最经典的, 将非 SSA 形式 IR 转换到 SSA 形式的算法.

当然你可能会问, 为什么非要先生成非 SSA 形式的 IR, 然后再把它转换到 SSA 形式呢? 不能一步到位直接生成 SSA 形式吗? 答案是可以的, 你可以参考论文: [*Braun et al. 2013, "Simple and Efficient Construction of Static Single Assignment Form"*](https://doi.org/10.1007%2F978-3-642-37051-9_6), 其中介绍的算法要比 Cytron 文章中的算法简单很多, 很适合 on-the-fly.

## SSA 形式上的优化

我们挑选了一些可以实现在你的编译器中的, 基于 SSA 形式的优化, 供你参考. 这些优化总体按照由易到难的顺序排列. 你可以查阅相关书籍, 文章, 或者 STFW, 来了解这些优化的相关内容和具体实现.

* 比较 naive 的, 考虑了 $\phi$ 函数的 DCE, 常量传播等优化.
* 考虑 $\phi$ 函数的归纳变量强度削弱.
* 各类利用 SSA 性质的寄存器分配算法.
* 稀疏条件常量传播 (SCCP).
* 全局值标号 (GVN).
* 基于 SSA 形式的部分冗余消除 (PRE), 这个比较难实现, 不是很推荐.
