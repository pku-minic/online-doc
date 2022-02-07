# Lv9.3. 数组参数

本节新增/变更的语法规范如下:

```ebnf
FuncFParam ::= BType IDENT ["[" "]" {"[" ConstExp "]"}];
```

## 一个例子

```c
int f(int arr[]) {
  return arr[1];
}

int main() {
  int arr[2] = {1, 2};
  return f(arr);
}
```

## 词法/语法分析

针对本节发生变化的语法规则, 设计新的 AST, 并更新你的 parser 实现即可.

## 语义分析

函数的数组参数中, 数组第一维的长度省略不写, 后序维度的长度是常量表达式, 你需要在编译时求出它们的值.

此外, 在本节中, 数组是可以被部分解引用的, 但得到的剩余部分的数组只能用来作为参数传入函数. 如果你进行了类型相关的检查, 你应该处理这种情况.

## IR 生成

回忆一下 C 语言的相关内容: 函数形式参数中的 `int arr[]`, `int arr[][10]` 等, 实际上表示的是指针, 也就是 `int *arr` 和 `int (*arr)[10]`, 而不是数组. SysY 中的情况与之类似.

那么如何在 IR 中表示这种参数呢? 看了前几节的内容, 你不难得出结论: 在一个类型之前添加 `*` 就可以表示这个类型的指针类型. 所以 `int arr[]` 和 `int arr[][10]` 对应的类型分别为 `*i32` 和 `*[i32, 10]`.

那么现在问题来了: 如果我们想读取 `int arr[]` 的第二个元素, 即得到 `arr[1]` 的值, 对应的 Koopa IR 该怎么写? `getelemptr` 此时已经不好使了, 因为它要求指针必须是一个数组指针, 而 `arr` 是一个整数的指针. 为了应对这种情况, 我们引入了另一种指针运算指令: `getptr`.

`getptr ptr, index` 指令执行了如下操作: 假设指针 `ptr` 的类型是 `*T`, 指令会算出一个新的指针, 这个指针的值是 `ptr + index * sizeof(T)`, 但类型依然是 `*T`. 在逻辑上, 这种操作和 C 语言中指针运算的操作是完全一致的. 比如:

```c
int *arr;   // 和 int arr[] 形式的参数等价
arr[1];
```

翻译到 Koopa IR 就是:

```koopa
@arr = alloc *i32         // @arr 的类型是 **i32
%ptr1 = load @arr         // %ptr1 的类型是 *i32
%ptr2 = getptr %ptr1, 1   // %ptr2 的类型是 *i32
%value = load %ptr2       // %value 的类型是 i32
// 这是一段类型和功能都正确的 Koopa IR 代码
```

本质上相当于:

```c
int *arr;
int *ptr = arr + 1;   // 注意这是 C 中的指针运算
*ptr;
```

对于数组的指针也同理:

```c
int (*arr)[3];
arr[1][2];
```

翻译到 Koopa IR 就是:

```koopa
@arr = alloc *[i32, 3]        // @arr 的类型是 **[i32, 3]
%ptr1 = load @arr             // %ptr1 的类型是 *[i32, 3]
%ptr2 = getptr %ptr1, 1       // %ptr2 的类型是 *[i32, 3]
%ptr3 = getelemptr %ptr2, 2   // %ptr3 的类型是 *i32
%value = load %ptr3           // %value 的类型是 i32
// 这是一段类型和功能都正确的 Koopa IR 代码
```

`getptr` 的规则就是如此, 你可以用它和 `getelemptr` 组合出和 SysY 数组相关的任意指针运算. 事实上, 如果你对 LLVM IR 有所了解, 你会发现 Koopa IR 中的 `getptr` 和 `getelemptr` 指令, 就是照着 LLVM IR 中的 `getelementptr` 指令设计的 (把这条指令拆成了两条指令), 但后者更为复杂, 对初学者而言很不友好.

综上所述, 示例程序生成的 Koopa IR 为:

```koopa
fun @f(@arr: *i32): i32 {
%entry:
  %arr = alloc *i32
  store @arr, %arr
  %0 = load %arr
  %1 = getptr %0, 1
  %2 = load %1
  ret %2
}

fun @main(): i32 {
%entry:
  @arr = alloc [i32, 2]
  %0 = getelemptr @arr, 0
  store 1, %0
  %1 = getelemptr @arr, 1
  store 2, %1
  // 传递数组参数相当于传递其第一个元素的地址
  %2 = getelemptr @arr, 0
  %3 = call @f(%2)
  ret %3
}
```

## 目标代码生成

前文已经描述过 `getptr` 的含义了, 它所做的操作和 `getelemptr` 在汇编层面完全一致, 所以你不难自行得出生成目标代码的方法.

本节乃至本章的指针运算较多, 建议你在编码时时刻保持头脑清晰.
