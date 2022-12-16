docker build -t combine-image .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 001057775987.dkr.ecr.us-east-1.amazonaws.com

REM aws ecr create-repository --repository-name combine-image --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag  combine-image:latest 001057775987.dkr.ecr.us-east-1.amazonaws.com/combine-image:latest
docker push 001057775987.dkr.ecr.us-east-1.amazonaws.com/combine-image:latest