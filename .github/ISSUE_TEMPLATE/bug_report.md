---
name: Bug report
about: Create a bug report to help us improve IAdrive
title: 'Bug report: '
labels: bug
assignees: ''

---

**Checklist**

# If you just delete all this text and post an issue it will be closed on sight.

Carefully read and work through this check list in order to prevent the most common mistakes and misuse of IAdrive, put x into all relevant boxes (like this [x])

- [ ] I understand IAdrive and its maintainers are not affiliated with Internet Archive or Google
- [ ] I understand IAdrive is merely a middleman between `gdown` and `internetarchive`, and relies on said package dependencies functioning properly, for example: Google Drive access restrictions, rate limiting, authentication issues, and Internet Archive outages are beyond the control of the maintainers of IAdrive
- [ ] I've updated `iadrive`, `gdown` and `internetarchive` along with their associated dependencies to their latest stable versions
- [ ] I've included the full and unredacted Google Drive URL and console output (with the exception of personal information or sensitive data), I understand hiding URLs will get the issue closed on sight
- [ ] I've checked that all provided Google Drive URLs are accessible, shareable, and have proper permissions set (publicly viewable or shared with appropriate access)
- [ ] I've searched the issues (closed or open) for similar bug reports, not just here on IAdrive, but [gdown's issue tracker](https://github.com/wkentaro/gdown/issues) for download issues and [internetarchive's issue tracker](https://github.com/jjjake/internetarchive/issues) for upload issues similar to mine
- [ ] I'm not submitting a bug report about Internet Archive S3 timeouts or Google Drive rate limiting, We have no control over Internet Archive outages, per-user throttling, or Google Drive API limitations, and sometimes these services have maintenance like hard disk swaps or temporary restrictions
- [ ] I've checked the [Internet Archive Twitter/X account](https://x.com/internetarchive) for any announced outages or planned infrastructure maintenance that would affect performance of uploads.
- [ ] I've verified that my Internet Archive account is properly configured by running `ia configure` and that I can upload to archive.org manually
- [ ] I have properly indented [with triple backticks - the key directly below Escape on a QWERTY keyboard - before and after the console output](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#quoting-code) full terminal output from the line where the command was run to where I was returned to command prompt, and am not trying to obscure item identifiers or URLs used in the creation of the bug (we need this to recreate the bug or investigate what happened)

**Dependency versions**

Please provide version information from core dependencies:

gdown version:
```
python -c "import gdown; print(gdown.__version__)"
```

`internetarchive` python client version:
```
ia --version
```

IAdrive version:
```
iadrive --version
```

Python version:
```
python --version
```

**System Information**
- Operating System: [e.g., Windows 11, Ubuntu 22.04, macOS 26]
- Python installation method: [e.g., system package, pyenv, conda, Microsoft Store]

**Google Drive URL**
Provide the exact Google Drive URL that's causing issues:
```
https://drive.google.com/...
```

**Wanted behavior**
A clear description of what you wanted to happen

**Actual behavior**
A clear description of what actually happened

**Console output**
Please paste the complete console output here:
```
[Paste your complete terminal output here, from the command you ran until you were returned to the prompt]
```

**Additional context**
Add any other context about the problem here:
- File/folder size
- Number of files in the folder
- Any special characters in filenames
- Whether this worked before
- Any error messages you've seen

---

> this template was provided by bibanon from tubeup and edited by Andres99 from iadrive