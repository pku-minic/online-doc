# 5.1. 提交代码

你可以使用我们提供的代码托管平台 ([eduxiji.gitlab.net](https://gitlab.eduxiji.net)) 来托管你实现的编译器的源代码. 当然, 你也可以使用其他代码托管平台, 评测系统中并不对此作强制要求.

## 使用平台托管代码

各位可以使用发放的账号登录代码托管平台, 然后新建 repo. 之后你就可以按照使用 Git 的一般流程来向代码托管平台提交代码了.

> 注意: 请务必将你创建的 repo 的可见性设为 “Private”, 否则所有人都将在平台上看到你提交的代码!

在进行评测之前, 你需要**创建一个 Deploy Token**, 以便平台能够借此访问到你创建的 private repo, 并从中拉取代码.

1. 首先, 你需要在浏览器中打开你的 repo, 并在侧边栏中选择 “Settings -> Repository”.

    ![step-1](token-step-1.png)

2. 找到 “Deploy Tokens”, 并展开.

    ![step-2](token-step-2.png)

3. 为你要创建的 token 填写名称, 过期时间, 用户名等信息. 勾选 “read_repository”, 确保创建的是一个只读的 token.

    ![step-3](token-step-3.png)

4. 点击 “Create deploy token” 按钮创建 token, 妥善保管创建得到的 token. **千万不要让别人得到你的 token**, 否则他们也可以根据这个 token 访问 repo 中的代码.

    ![step-4](token-step-4.png)

5. 将刚刚填写的用户名和创建得到的 token 拼接为 repo 的 URL, 格式为:

    ```
    https://<token_username>:<deploy_token>@gitlab.eduxiji.net/<username>/<repo_name>.git
    ```

    在本例中为:

    ```
    https://MaxXing:-5dzfbjLsYsstYACyT2T@gitlab.eduxiji.net/MaxXing/pku-minic-test.git
    ```

6. 在本地测试上述 URL 确实可用. 你可以尝试使用 `git` 命令 clone 这个 URL:

    ```
    $ git clone https://MaxXing:-5dzfbjLsYsstYACyT2T@gitlab.eduxiji.net/MaxXing/pku-minic-test.git
    Cloning into 'pku-minic-test'...
    remote: Enumerating objects: 90, done.
    remote: Counting objects: 100% (90/90), done.
    remote: Compressing objects: 100% (89/89), done.
    remote: Total 90 (delta 21), reused 0 (delta 0), pack-reused 0
    Unpacking objects: 100% (90/90), done.
    ```

通过完成以上步骤, 你就可以创建一个可供提交使用的 token 及其对应的 URL 了.

## 使用 GitHub 托管代码

如果你决定使用 GitHub 而非我们提供的平台托管自己的代码, 并且你的 repo 的可见性也为 private, 则你同样需要执行类似上述的流程, 比如创建一个 personal access token.

建议你在评测平台中提交自己 repo 的 URL 之前, 先在本地 `git clone` 验证这个 URL 的确可用, 以防线上的评测系统无法 clone 你的 repo.
