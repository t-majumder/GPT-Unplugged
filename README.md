# Research_gpt
<img width="1584" height="396" alt="Untitled design (1)-modified" src="https://github.com/user-attachments/assets/5edb7f80-085a-455f-b06e-c6574c8f9d68" />

An Open-source, **Interconnected Local server-based GPT assistant** for **maximum privacy**. **Giving you the ultimate control of your data**.

## ✨ Features

-  **Complete Privacy**: All data stays local on your machine
-  **Integrated Free Grok API**: No subscription required
-  **Cross-Device Access**: Use Tailscale to access the service across devices in your local network
-  **Multi-Platform**: Full support for PC, mobile, and tablet devices
-  **Ollama Integration**: Host models locally for complete independence
-  **Model Supports**: **Qwen 32B** , **GPT OSS 120B** , **Kimi K2 Instruct** ,  **LLama 3.3 70B** ,
- **Upcoming**: **Ollama model api integration (TBD)**
   
### PC Integration

<img width="1909" height="904" alt="Screenshot 2025-11-29 194117-modified" src="https://github.com/user-attachments/assets/e68edb7f-59a2-4cdb-bf9f-d8af60dca062" />

### Mobile and tab integration
<div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
  <img src="https://github.com/user-attachments/assets/56132c4e-061f-4f1b-8804-bb6e3125e62f" style="height: 370px; flex: 1; object-fit: contain;">
  <img src="https://github.com/user-attachments/assets/68989f8f-2dfb-4051-80ab-5c9ad90956b2" style="height: 370px; flex: 1; object-fit: contain;">
</div>

## 📦 Installation

### Prerequisites

- Docker installed on your system
- A Grok API account (free)

### Step 1: Get Your Grok API Key

1. Create a Grok account at [Grok AI](https://grok.x.ai)
2. Generate your API key from the dashboard

### Step 2: Configure Environment Variables

Create a `.env` file in the project root directory and add your API key:

```env
GROK_API_KEY="your_api_key_here"
```

### Step 3: Build Docker Image

Open command prompt/terminal in the project folder and run:

```bash
docker build -t research_gpt .
```

## 🎯 Usage

### Running the Application

Start the application using Docker:

```bash
docker run -p 8000:8000 research_gpt
```
<img width="1269" height="717" alt="Screenshot 2025-11-29 180152-modified" src="https://github.com/user-attachments/assets/ac594b25-5efa-4723-926b-248d214e3597" />

### Accessing the Interface

Open your browser and navigate to:

```
http://localhost:8000
```

That's it! You're ready to use Research_gpt.
### Sample Outputs
<img width="1914" height="874" alt="Screenshot 2025-11-29 194854-modified" src="https://github.com/user-attachments/assets/4afea833-30e2-470e-8269-af81d153e232" />

<img width="1912" height="905" alt="Screenshot 2025-11-29 194917-modified" src="https://github.com/user-attachments/assets/01f619b3-ac06-45c9-aea2-9076b372a2fc" />

## 🔧 Advanced Configuration

### Using Tailscale for Remote Access

To access Research_gpt from other devices on your network:

1. Install [Tailscale](https://tailscale.com) on all devices
2. Connect your devices to the same Tailscale network
3. Access the application using your Tailscale IP

### Ollama Integration

For local model hosting with Ollama:

1. Install [Ollama](https://ollama.ai)
2. Configure the Ollama API endpoint in your settings
3. Start hosting models locally for complete privacy

## 📄 License
MIT Liscense

## ⭐ Support

If you find this project useful, please consider giving it a star on GitHub!

---

**Note**: This project prioritises your privacy. All data processing happens locally on your machine, and you maintain complete control over your information.
