<p align="center">
  <a href="https://dev.to/vumdao">
    <img alt="Serverless - Shorten Long URL" src="https://cdn.hashnode.com/res/hashnode/image/upload/v1612715469916/vdgs_kQ2o.jpeg" width="500" />
  </a>
</p>
<h1 align="center">
  <div><b>Serverless - Shorten Long URL</b></div>
</h1>

### - There are many web apps provide the service of shortening your long url (free or charge). This ariticle introduces the way of using serverless with Cloud development toolkit (CDK)

### - CDK helps to create this project by coding (python language), What's its benefits?
###   + Infra structure as code
###   + Update lambda function code and just need to execute `cdk deploy`, all the code and modules will be up-to-date
###   + Create and destroy the structure quickly, and we can manage the structure by separate stacks such dynamodb stack, IAM stack, lambda stack and API Gateway stack.


![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612715356287/xIxqONMut.png)

## What’s In This Document 
- [Init CDK project](#-Init-CDK-project)
- [Create source code](#-Create-source-code)
- [Deploy stacks](#-Deploy-stacks)
- [Demo](#-Demo)

### 🚀 **[Init CDK project](#-Init-CDK-project)**
```
⚡ $ mkdir shorten-url
⚡ $ cd shorten-url
⚡ $ cdk init -l python
```

### 🚀 **[Create source code](#-Create-source-code)**
- Source: [shorten-url](https://github.com/vumdao/shorten-url)
```
⚡ $ tree
.
├── app.py
├── create_src
│   └── createShortUrl.py
├── README.md
├── redirect_src
│   └── redirectUrl.py
├── requirements.txt
├── setup.py
├── shorten_url
│   ├── __init__.py
│   └── shorten_url_stack.py
```

- Add python boto3 module for lambda function sources
```
⚡ $ pip install boto3 -t create_src
⚡ $ pip install boto3 -t redirect_src
```

- Cdk synth to check cdk valid
```
⚡ $ cdk synth
Successfully synthesized to ~/shorten-url/cdk.out
Supply a stack id (ShortenUrlDDB, ShortenUrlIAMRole, ShortenURLCreateLambda, ShortenURLRedirectLambda, ShortenURLApiGW) to display its template.
```

- List stacks
```
⚡ $ cdk ls
ShortenUrlDDB
ShortenUrlIAMRole
ShortenURLCreateLambda
ShortenURLRedirectLambda
ShortenURLApiGW
```

### 🚀 **[Deploy stacks](#-Deploy-stacks)**
```
⚡ $ cdk deploy '*'
```

- Full stacks created in cloudformation:
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612709323826/R0QmcS1ZL.png)

- Lambda functions:
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612710406792/MY9Bwp4mO.png))

- Lambda function: create url
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612713128773/JHVAygCl2.png))

- Lambda function: redirect url
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612713136755/l6Eyj1Hvt.png)

- API Gateway
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612713453681/1nA0pNxAH.png)
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612713460723/YyHV7PtLE.png)

### 🚀 **[Demo](#-Demo)**
- POST a long url (here is not actually long)
```
⚡ $ curl -L -X POST 'https://s.cloudopz.co/shortenUrl' -H 'Content-Type: application/json' --data-raw '{"url": "https://hashnode.com/@vumdao"}'
"{\"short_url\": \"https://s.cloudopz.co/dVkiBRM\"}"
```

- Check dynamodb table
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612713746847/DgS12ODSj.png)
    - Note that I add `expiry_date` attribute for TTL = 7 days

- Click on the short URL
![Alt Text](https://cdn.hashnode.com/res/hashnode/image/upload/v1612714008725/pEkrY51Oe.png)


<h3 align="center">
  <a href="https://dev.to/vumdao">:stars: Blog</a>
  <span> · </span>
  <a href="https://vumdao.hashnode.dev/">Web</a>
  <span> · </span>
  <a href="https://www.linkedin.com/in/vu-dao-9280ab43/">Linkedin</a>
  <span> · </span>
  <a href="https://www.linkedin.com/groups/12488649/">Group</a>
  <span> · </span>
  <a href="https://www.facebook.com/CloudOpz-104917804863956">Page</a>
  <span> · </span>
  <a href="https://twitter.com/VuDao81124667">Twitter :stars:</a>
</h3>
