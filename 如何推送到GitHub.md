# 🚀 UniCore 推送到 GitHub

## 方法一：在您自己的电脑上（推荐）

### 步骤 1：下载代码
把这个项目的所有文件下载到您的电脑

### 步骤 2：安装 GitHub CLI
```
Windows:  winget install GitHub.cli
Mac:      brew install gh
Linux:    sudo apt install gh
```

### 步骤 3：登录 GitHub
```
gh auth login
```
按提示操作，会打开浏览器让您授权

### 步骤 4：推送
```
cd UniCore
./push_to_github.sh 你的用户名
```

---

## 方法二：手动推送

```bash
# 1. 登录 GitHub
gh auth login

# 2. 创建仓库
gh repo create UniCore --public

# 3. 推送代码
cd UniCore
git remote add origin https://github.com/你的用户名/UniCore.git
git push -u origin master
```

---

## 方法三：直接在 GitHub 网页创建

1. 打开 https://github.com/new
2. 创建新仓库 "UniCore"
3. 把代码文件上传上去

---

## ✅ 推送后

您的 UniCore 项目就会出现在：
https://github.com/你的用户名/UniCore

然后告诉我仓库地址，我就可以：
- 帮你更新代码
- 创建新功能
- 修复问题
- 等等
