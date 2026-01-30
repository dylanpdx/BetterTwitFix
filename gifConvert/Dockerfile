FROM public.ecr.aws/lambda/python:3.12 AS builder
RUN dnf -y install git cargo && dnf clean all
RUN git clone https://github.com/ImageOptim/gifski /gifski
WORKDIR /gifski
RUN cargo build --release

FROM public.ecr.aws/lambda/python:3.12 AS ffmpeg
RUN dnf -y update
RUN dnf -y install git wget tar.x86_64 xz && dnf clean all
WORKDIR /ffmpeg
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
RUN tar -xvf ffmpeg-release-amd64-static.tar.xz


FROM public.ecr.aws/lambda/python:3.12
COPY --from=builder /gifski/target/release/gifski ./
COPY --from=ffmpeg /ffmpeg/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffmpeg/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ffprobe
RUN pip install requests==2.32.3

# Copy function code
COPY __init__.py ${LAMBDA_TASK_ROOT}/app.py

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.lambda_handler" ] 