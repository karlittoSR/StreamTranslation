# GitHub Clone & Run Guide

Chinese / English / Japanese

---

## For Chinese streamers

### 第一步：获取API密钥 (Step 1: Get API Keys)

#### OpenAI API
1. 访问 https://platform.openai.com/api-keys
2. 创建新的 Secret Key
3. 复制密钥（以 `sk-` 开头）

#### DeepL API
1. 访问 https://www.deepl.com/pro/account
2. 注册免费账户（不需要信用卡）
3. 转到 API 密钥部分
4. 复制你的免费 API 密钥

#### Azure (可选备用)
- 只有当 DeepL 配额用完时才需要
- 现在可以跳过

### 第二步：克隆并设置 (Step 2: Clone & Setup)

打开 PowerShell：

```powershell
# 克隆仓库
git clone https://github.com/karlittoSR/StreamTranslation.git
cd StreamTranslation

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 第三步：配置 API 密钥 (Step 3: Configure API Keys)

```powershell
# 复制示例文件
Copy-Item .env.example .env

# 用记事本编辑
notepad .env
```

粘贴你的 API 密钥：
```
OPENAI_API_KEY=sk-your-openai-key
DEEPL_AUTH_KEY=your-deepl-key
AZURE_AUTH_KEY=skip-for-now
```

保存并关闭。

### 第四步：配置语言 (Step 4: Configure for Chinese)

编辑 `live_subs.py` 文件，找到 `transcribe_audio()` 函数（大约第 600 行）：

找到这一行：
```python
language="fr",
```

改为：
```python
language="zh",
```

然后编辑 Config 类中的 `transcription_prompt`（大约第 40 行）：

```python
transcription_prompt: str = (
	"You are transcribing Chinese gamer speech from a live stream. "
	"Context: speedrunning and gaming. Remove filler words. "
	"If you can't understand, leave blank."
)
```

### 第五步：找到你的麦克风 (Step 5: Find Your Microphone)

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

输出示例：
```
  0 - Speakers (扬声器)
  1 - Microphone (麦克风) <-- 记住这个数字
  2 - Headset (耳机)
```

编辑 `live_subs.py` 第 38 行：
```python
input_device_index: int = 1  # 改为你的麦克风编号
```

### 第六步：OBS 设置 (Step 6: Set Up OBS)

1. 打开 OBS Studio
2. 添加Source → **Text (GDI+)**
3. 名称：`Subtitles`
4. ✓ 勾选 **"Read from file"**
5. 点击 **Browse** → 选择 `subs_en.txt`
6. 字体大小：`32-48pt`
7. 位置：屏幕底部
8. 点击 **OK**

### 第七步：测试 (Step 7: Test)

```powershell
python live_subs.py
```

你应该看到：
```
🎤 Starting live subtitle transcription
   Device: 1, Sample rate: 16000 Hz
   🌍 DeepL translation enabled -> EN-US
```

**对着麦克风说话！**

2 秒沉默后，你会看到：
- 控制台：`FR: 你好 [EN: Hello]`
- OBS 显示：`Hello`

按 `Ctrl+C` 停止。

---

## Detailed Documentation

- **快速入门 (Quick Start):** `QUICKSTART.md`
- **完整指南 (Full Guide):** `README.md`
- **贡献指南 (Contributing):** `CONTRIBUTING.md`
- **更新日志 (Changelog):** `CHANGELOG.md`

---

## Troubleshooting

### "No module named openai"
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --upgrade
```

### "DEEPL_AUTH_KEY not set"
- 你创建了 `.env` 文件吗？（不是 `.env.example`）
- 你粘贴了实际的密钥吗？
- 重启 PowerShell

### 没有听到任何音频
```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```
确保 `input_device_index` 是正确的麦克风编号。

### OBS 中没有显示字幕
- Text source: ✓ 勾选 "Read from file"
- 验证路径指向 `subs_en.txt`
- 重启 OBS

### 错误的语言被转录
- 对于中文：将 `language="fr"` 改为 `language="zh"`
- 对于其他语言：改为你想要的语言代码

---

## Cost Summary

| 服务 | 月成本 |
|------|-------|
| OpenAI Whisper | ~$12 |
| DeepL | $0 (免费层) |
| Azure | $0 (仅当需要时) |
| **总计** | **~$12** |

非常便宜！

---

## Daily Usage

一旦设置完成：

```powershell
cd C:\Your\Path\To\StreamTranslation
.\venv\Scripts\Activate.ps1
python live_subs.py
```

在 OBS 中开始流式传输 - 字幕会自动显示！

---

## Supported Languages

**转录语言：**
- `fr` - 法语 (French)
- `zh` - 中文 (Chinese)
- `en` - 英语 (English)
- `es` - 西班牙语 (Spanish)
- `de` - 德语 (German)
- `ja` - 日语 (Japanese)
- 还有更多...

**翻译语言代码：**
- `EN-US` - 英语（美国）
- `EN-GB` - 英语（英国）
- `ZH` - 中文
- `DE` - 德语
- `FR` - 法语
- 等等...

---

## What's Next?

1. 创建 `glossary.json` 以修复常见的误译
2. 调整 `vad_energy_threshold` 如果拾取太多背景噪音
3. 自定义 OBS 文本源的颜色/字体
4. 在流媒体中使用！

---

## Questions?

1. 查看 `README.md`
2. 查看 `QUICKSTART.md`
3. 在 GitHub Issues 中提问
4. 检查你的 API 密钥是否正确

---

## File Structure

```
StreamTranslation/
├── live_subs.py          # 主脚本 (Main script)
├── requirements.txt      # Python 依赖 (Dependencies)
├── .env.example          # API 密钥模板 (API keys template)
├── .gitignore           # Git 忽略规则 (Git ignore rules)
├── setup.ps1            # Windows 自动化设置 (Setup script)
├── README.md            # 完整文档 (Full guide)
├── QUICKSTART.md        # 快速入门 (Quick start)
├── config_example.yaml  # 配置示例 (Config example)
├── glossary_example.json # 词汇示例 (Glossary example)
├── CHANGELOG.md         # 更新日志 (Changelog)
└── CONTRIBUTING.md      # 贡献指南 (Contributing guide)
```

---

## Community

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and general help
- Code comments: Explain complex logic

---

Happy streaming!
