docker build -t tw-extract .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 001057775987.dkr.ecr.us-east-1.amazonaws.com

REM aws ecr create-repository --repository-name tw-extract --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag  tw-extract:latest 001057775987.dkr.ecr.us-east-1.amazonaws.com/tw-extract:latest
docker push 001057775987.dkr.ecr.us-east-1.amazonaws.com/tw-extract:latest