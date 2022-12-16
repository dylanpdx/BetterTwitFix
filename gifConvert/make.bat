docker build -t gif-convert .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 001057775987.dkr.ecr.us-east-1.amazonaws.com

REM aws ecr create-repository --repository-name gif-convert --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag  gif-convert:latest 001057775987.dkr.ecr.us-east-1.amazonaws.com/gif-convert:latest
docker push 001057775987.dkr.ecr.us-east-1.amazonaws.com/gif-convert:latest