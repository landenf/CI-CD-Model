# Mock CI/CD Pipeline - Proof of Concept

### Project Outline: 
This project revolves around a Continuous Integration and Continuous Delivery pipeline built using AWS CodePipline and other AWS microservices. The CI/CD pipeline is a proof-of-concept project showcasing the possibility of seamlessly integrating DevOps practices into development teams. This serves to automate the software development lifecycle, encompassing developer implementation, code review (Git), code build, testing, and deployment, and final staging stakeholder approval.

### Why? 
AWS offers a surplus of configuration options for CI/CD through their CodePipline including complicated build, test, and deploy processes. This pipeline incorporates all of these features in addition to the manual approval process AWS offers. HOWEVER, the idea for not only demonstrating this process but also building a custom feature came about when wondering what about non-technical individuals in the process. Stakeholders, non-technical PMs, and other personnel involved in approving staging environments or new features deployed should be able to be involved in the automation process. This pipeline creates a workaround for this process by utilizing AWS microservices in addition to the pipeline.

### Setup - Microservices Involved

AWS Microservices Used
- AWS Lambda
    - Url Generator Funtion
    - Url Validation Function
- AWS DynamoDB
    - Table entries hold outstanding request approval tokens.
- AWS Code Pipeline
- AWS Code Commit
    - Configured to read from Git
- AWS Code Build
- AWS Code Deploy
    - Staging and Live environments
- AWS SNS 
    - Approval Topic (FIFO)
        - Pub: Lambda
        - Sub: SES
- AWS SES
    - Configured to the Stakeholder email list

Note: Repo clone is not necessary. 
Copy Python scripts into lambda functions and configure microservices and permissions.

## Diagram of Project Architecture

  - Flowchart
  
   ```mermaid
     graph TD;
         A-->B;
         A-->C;
         B-->D;
         C-->D;
   ```

## Step 1 – Code Implementation and Review  --  (Walkthrough)

### Git
In this phase, a developer codes for a designated task and initiates a pull request. A peer or senior developer reviews and approves the changes. Upon approval, the pull request is merged into the deployment-bound branch.

## Step 2 – Build and Deploy (Staging)

### AWS Code Commit

CodeCommit uses a GitHub webhook to monitor a Git branch's status. Whenever code changes are detected, it fetches the source code, generates essential artifacts, and triggers the pipeline.

### AWS Code Build
This stage leverages AWS CodeBuild to compile the code using previously generated artifacts. Upon a successful build, the pipeline advances to the next stage.

### AWS Code Deploy 
This stage grabs the successful build artifacts and code changes and deploys them to the configured deployment group. This could be an EC2 instance, ECS, or even on-premise servers. For this step, the changes will be deployed to a staging environment. 

## Step 3 – Stakeholder Approval

### Step Outline: 
Part of the software development lifecycle is obtaining approval when code changes are made. This often is required from non-technical roles (i.e. Stakeholders, administrative roles, or non-technical product managers). To accommodate this, a manual approval checkpoint is integrated into the pipeline to assess the changes deployed to staging servers. However, to not require access to the AWS console or CLI (for those non-technical roles) this process was built manually using a combination of microservices. 

### Implementation
AWS Pipeline publishes a message to the SNS topic which has an AWS Lambda function attached as a subscriber to the topic. This lambda function uses environment variables, information from the pipeline request message, and AWS clients to send an email to the configured “Stakeholder” email address. Since this function generates its own unique accept and reject tokens added to the approval URL these tokens are stored in an AWS DynamoDB table. This table consists of a message ID, accept code, reject code, pipeline name, stage, and token. 

The stakeholder will receive an email (using verified SES addresses) including the link to review the staging site as well as a reject and accept URL. This URL is the function URL associated with another Lambda function responsible for validating the token/code as well as pushing the pipeline forward. This function checks the code against the DynamoDB table and publishes an approval result to the AWS Pipeline. Applicable IAM roles and policies implemented to allow permissions. 

## Step 4 – Production Deployment

Once all the pipeline steps are complete and the changes are approved by stakeholders this step grabs the same build artifacts from the last deployment and deploys them to the live servers for production. Various deployment strategies such as blue/green, canary, or linear can be configured based on requirements. If the build fails, or the approval is rejected the pipeline is halted until the change is fixed and re-checked into the source control. 