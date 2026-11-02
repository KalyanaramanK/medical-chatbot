# Build-a-Complete-Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS

# How to run?
### STEPS:

Clone the repository

```bash
git clonehttps://github.com/entbappy/Build-a-Complete-Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS.git
```
### STEP 01- Create a conda environment after opening the repository

```bash
conda create -n medibot python=3.10 -y
```

```bash
conda activate medibot
```


### STEP 02- install the requirements
```bash
pip install -r requirements.txt
```


### Create a `.env` file in the root directory and add your Groq credentials:

```ini
GROQ_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# Optional; defaults to openai/gpt-oss-120b
GROQ_MODEL = "openai/gpt-oss-120b"
```


```bash
# run the following command to store embeddings to pinecone
python store_index.py
```

```bash
# Finally run the following command
python app.py
```

Now,
```bash
open up localhost:
```

### Deploy the frontend to Firebase and the backend to Render

Firebase Hosting serves the static chat page, while Render runs the Flask API.
This keeps Firebase on the Spark plan; do not deploy Cloud Functions for this
setup. The Render Blueprint uses a Standard instance because the sentence
transformer embedding model needs more memory than a free instance provides.

1. Push this project to a GitHub repository. Do not commit `.env`; it is ignored.
2. In Render, create a Blueprint from that repository and select `render.yaml`.
   Set `GROQ_API_KEY`, `QDRANT_URL`, and `QDRANT_API_KEY` as the prompted secret
   environment variables. Wait for the service health check to pass.
3. Copy the Render service URL (for example,
   `https://medical-chatbot-api.onrender.com`) into `static/config.js`:

   ```js
   window.CHATBOT_API_BASE_URL = "https://medical-chatbot-api.onrender.com";
   ```

4. Deploy only the static Hosting site. From the project root, sign in with the
   Firebase CLI if needed, then run:

   ```bash
   npx firebase-tools login
   npx firebase-tools deploy --only hosting --project chatbot-887c5
   ```

5. Open the Hosting URL printed by Firebase. The allowed Firebase origins are
   configured in `render.yaml`; update `FRONTEND_ORIGINS` there if you use a
   custom Hosting domain, then redeploy the Render service.

For local development, leave `CHATBOT_API_BASE_URL` empty; the page served by
Flask will send chat requests to the same origin. Keep the `.env` file local and
enter its required credentials in Render's environment settings instead.


### Techstack Used:

- Python
- LangChain
- Flask
- GPT
- Pinecone



# AWS-CICD-Deployment-with-Github-Actions

## 1. Login to AWS console.

## 2. Create IAM user for deployment

	#with specific access

	1. EC2 access : It is virtual machine

	2. ECR: Elastic Container registry to save your docker image in aws


	#Description: About the deployment

	1. Build docker image of the source code

	2. Push your docker image to ECR

	3. Launch Your EC2 

	4. Pull Your image from ECR in EC2

	5. Lauch your docker image in EC2

	#Policy:

	1. AmazonEC2ContainerRegistryFullAccess

	2. AmazonEC2FullAccess

	
## 3. Create ECR repo to store/save docker image
    - Save the URI: 315865595366.dkr.ecr.us-east-1.amazonaws.com/medicalbot

	
## 4. Create EC2 machine (Ubuntu) 

## 5. Open EC2 and Install docker in EC2 Machine:
	
	
	#optinal

	sudo apt-get update -y

	sudo apt-get upgrade
	
	#required

	curl -fsSL https://get.docker.com -o get-docker.sh

	sudo sh get-docker.sh

	sudo usermod -aG docker ubuntu

	newgrp docker
	
# 6. Configure EC2 as self-hosted runner:
    setting>actions>runner>new self hosted runner> choose os> then run command one by one


# 7. Setup github secrets:

   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_DEFAULT_REGION
   - ECR_REPO
   - PINECONE_API_KEY
   - OPENAI_API_KEY
