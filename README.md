<p align="center">
  <img src="frontend/images/Logo.png" alt="Theme" width="450">

<!-- stars and logos -->

<p align="center">
  <a href="https://github.com/t-majumder/GPT-Unplugged/stargazers">
    <img src="https://img.shields.io/github/stars/t-majumder/GPT-Unplugged?style=plastic&logo=github&logoColor=white" alt="GitHub stars">
  </a>

  <a href="https://x.com/dextro_rx">
    <img src="https://img.shields.io/badge/X-@dextro_rx-black?style=plastic&logo=x&logoColor=white" alt="X">
  </a>

  <a href="https://scholar.google.com/citations?user=7jXnxCkAAAAJ&hl=en">
    <img src="https://img.shields.io/badge/Scholar-Profile-4285F4?style=plastic&logo=google-scholar&logoColor=white" alt="Website">
  </a>

  <a href="https://github.com/t-majumder/GPT-Unplugged/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green?style=plastic&logo=open-source-initiative&logoColor=white" alt="MIT License">
  </a>
</p>

<!-- writeup -->
<p align="center">
  <strong>👋🏻 Hi everyone! GPT Unplugged🔌 an interconnected, local server-based, fully customizable, privacy-focused research agent.</strong><br>
  <strong>Ultimate control of your data and conversations.</strong>
</p>

<!-- customization image -->
<p align="center">
  <img src="/images/theme_selection.png" alt="Theme" width="800">
</p>

<p align="center">
<strong>Scenario 1 </strong>
</p>

Tomorrow if there is **No internet access** this can be your **Local personal assistant** with new knowledge. Feed it your documents or books or pdfs and keep the conversation rolling. It has **cross model memory** so none of your previous chat or context is lost in between. Switch moel and keep the conversation rolling.

<p align="center">
<strong>Scenario 2 </strong>
</p>  

In your **local network** just run on one machine and **use in all your personal devices**. All device under the same **WIFI** network. So basically your personal bot whom you have deep conversations with when youre sleepy or in bed... \
**(Watch the movie 'HER' you'll get the reference...)**


## ✨ Features
-  **Complete Privacy**: All data stays local on your machine
-  **Cross-Device Access**: Use Tailscale to access the service across devices in your local network
-  **Multi-Platform**: Full support for PC, mobile, and tablet devices
-  **Ollama Integration**: Host models locally for complete independence (Local inference for full independence)
-  **Model Supports**: **Qwen 32B** , **GPT OSS 20B** ,**GPT OSS 120B**, **Kimi K2 Instruct** ,  **LLama 3.3 70B** , **All Ollama Models**.
-  **Supports Multiturn, Long context memory, Rag, rerankers...**

# 📦 Installation
## Step 1️: Installing it. (One-time thing)
Create a new folder where you want everything to be stored. 
Open terminal inside the folder, and run these commands one after another(Inside the same terminal):
```bash
git clone https://github.com/t-majumder/GPT-Unplugged.git
cd GPT-Unplugged
python -m venv gpt
```

```bash
# choose based on your system

gpt\Scripts\activate      # For Windows run this
source gpt/bin/activate   # For Linux run this
```

```bash
pip install -r requirements.txt
```
#### Close everything. Installation is done.

## Step 2: Setting the free API key (After this technical stuff is done)
-> Go to the Groq website : https://console.groq.com/keys  (Get your free API key here) \
-> Paste your API key here. Go to -> 
```bash
GPT-Unplugged/
├── backend/
│   ├── .env    # Paste your GROQ API key here
```

# 🎯Running the project:
1) Go to the GPT-Unplugged folder.
2) Open terminal inside the folder and run this command based on Windows or Linux.
#### For Windows:
```bash
run run.ps1
```
#### For Linux:
```bash
run run.sh
```

Now you can access the website from your browser. (copy-paste this link inside your browser)
```bash
http://localhost:5173/
```

## 🔧 Advanced Configuration
You can configure the peompt (Behavior) and add models using the config files directly.
```bash
GPT-Unplugged/
├── config/
│   ├── prompt.yaml    # Add your custom prompt
│   ├── models.yaml    # Add the model name
│   ├── hyperparams.yaml    # Other hyperparams you can tune as well
```

<p align="center">
  <img src="/images/multidevice_support.png" alt="Theme" width="1000">
</p>

## 🦙 Ollama Integration

For local model hosting with Ollama:
Just install [Ollama](https://ollama.ai) and download the models. (done)
```bash
ollama run gemma3:4b
```
This command downloads the model. You can download and add other models as well...

## ⚡Local Server
To access Research_gpt from other devices on your network:

1. Install [Tailscale](https://tailscale.com) on all devices
2. Connect your devices to the same Tailscale network
3. Access the application using your Tailscale IP
```bash
http://Your Tailscale IP:5173/
```
<p align="center">
  <img src="/images/demo.png" alt="Theme" width="1000">
</p>

## 📄 License
MIT Liscense

## ⭐ Support
If you find this project useful, please consider giving it a star on GitHub!

---

**Note**: This project prioritises your privacy. All data processing happens locally on your machine, and you maintain complete control over your information.
