## Table of contents

[🖊️ Sign your commits with SSH keys in Github](#a)<br />
[Why is this important? 🤔](#b)<br />
[1️⃣ Prerequisites](#c)<br />
[2️⃣ Configure Git to sign commits with SSH](#d)<br />
[💻 Configure IntelliJ IDEA to sign commits automatically](#e)<br />
[3️⃣ Sign your commits](#f)<br />
[4️⃣ Verify on Github](#g)<br />
[✅ Final Checklist (Copy-Paste Ready)](#h)<br />
[🔗 Useful Links](#i)<br />

---

# <a id="a"></a> 🖊️ Sign your commits with SSH keys in Github

## <a id="b"></a> Why is this important? 🤔

- A signed commit proves it was really you who made it (authenticity).

- Github shows a green ✅ Verified label on your commits, so your teammates know it hasn’t been altered.

- Unsigned commits could be impersonated or tampered with more easily.

---

## <a id="c"></a> 1️⃣ Prerequisites

Before enabling signed commits, make sure you have:

- Git ≥ 2.34.0

- OpenSSH ≥ 8.1 (⚠️ avoid 8.7, it’s broken)

- An SSH key already added to Github with usage Authentication & Signing.

---

## <a id="d"></a> 2️⃣ Configure Git to sign commits with SSH

1. Tell Git to use SSH for commit signing:
```
git config --global gpg.format ssh
```

2. Point Git to your public key (.pub file):
```
git config --global user.signingkey ~/.ssh/<your_public_ssh_key_file>
```
👉 Replace with your actual key path if different.

---

## <a id="e"></a> 💻 Configure IntelliJ IDEA to sign commits automatically

If you’re using IntelliJ (or PyCharm, WebStorm, etc.), you can enable commit signing directly in the IDE.

1. Open Settings → File > Settings (or Ctrl + Alt + S)

2. Go to Version Control → Git → Commit

3. Check the box ✅ “Sign commits with GPG key”

💡 Even if you use SSH for signing, IntelliJ labels this option “GPG key”. It still works the same way.

4. If IntelliJ doesn’t detect your key automatically:

   - Click “GPG Key ID” and browse to your public key file

   - Make sure your ~/.gitconfig contains the Git config lines shown above

---

## <a id="f"></a> 3️⃣ Sign your commits

Now you can sign commits:
```
git commit -S -m "My signed commit"
```
- -S = sign this commit.
- You can also make Git always sign commits:
```
git config --global commit.gpgsign true
```

---

## <a id="g"></a> 4️⃣ Verify on Github

Push your signed commit:
```
git push
```
On Github, go to your repository → Commits.

- Signed commits show a green Verified badge ✅.

- Unsigned or invalid ones show Unverified ⚠️.

---

## <a id="h"></a> ✅ Final Checklist (Copy-Paste Ready)

**Setup (only once)**
```md
# 1. Use SSH for commit signing
git config --global gpg.format ssh

# 2. Tell Git which key to use
git config --global user.signingkey ~/.ssh/<your public key file>

# 3. Always sign commits (optional but recommended)
git config --global commit.gpgsign true
```

**Everyday usage**
```md
# Make a signed commit
git commit -m "My signed commit"

# Push to Github
git push
```

## <a id="i"></a> 🔗 Useful Links

Learn everything about signed commits:

[About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)
