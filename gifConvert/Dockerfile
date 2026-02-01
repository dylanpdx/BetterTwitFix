ARG TARGETARCH
FROM public.ecr.aws/lambda/python:3.12 AS builder
RUN dnf -y install git cargo && dnf clean all
RUN git clone https://github.com/ImageOptim/gifski /gifski
WORKDIR /gifski
RUN cargo build --release

#FROM public.ecr.aws/lambda/python:3.12 AS ffmpeg-linux-amd64
#RUN dnf -y update
#RUN dnf -y install git wget tar.x86_64 xz && dnf clean all
#WORKDIR /ffmpeg
#RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
#RUN tar -xvf ffmpeg-release-amd64-static.tar.xz

#FROM public.ecr.aws/lambda/python:3.12 AS ffmpeg-linux-arm64
#RUN dnf -y update
#RUN dnf -y install git wget tar xz && dnf clean all
#WORKDIR /ffmpeg
#RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz
#RUN tar -xvf ffmpeg-release-arm64-static.tar.xz

#FROM ffmpeg-linux-${TARGETARCH} AS ffmpeg

FROM public.ecr.aws/lambda/python:3.12 AS ffmpeg
# tl;dr: build ffmpeg from source with svt-av1 support and statically linked binaries

# Install dependencies
RUN dnf remove -y microdnf-dnf && microdnf install -y dnf
RUN dnf group install "Development Tools" -y

RUN mkdir /ffmpeg_sources
WORKDIR /ffmpeg_sources
RUN git clone https://git.ffmpeg.org/ffmpeg.git .
RUN git clone --branch stable --depth 1 https://code.videolan.org/videolan/x264.git
RUN git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git

RUN dnf install curl nasm glibc-static libstdc++-static cmake --allowerasing -y

# Install x264
WORKDIR /ffmpeg_sources/x264
RUN PKG_CONFIG_PATH="/ffmpeg_build/lib/pkgconfig" ./configure --prefix="/ffmpeg_build" --bindir="/bin" --enable-static
RUN make -j
RUN make install

# Install SVT-AV1
WORKDIR /ffmpeg_sources
WORKDIR /ffmpeg_sources/SVT-AV1/Build

RUN PKG_CONFIG_PATH="/ffmpeg_build/lib/pkgconfig" cmake .. -G"Unix Makefiles" -DCMAKE_BUILD_TYPE=Release -DENABLE_STATIC=ON -DBUILD_SHARED_LIBS=OFF -DCMAKE_C_FLAGS_INIT="-static"

RUN make -j
RUN make install

# Install FFmpeg
WORKDIR /ffmpeg_sources
RUN PKG_CONFIG_PATH="/ffmpeg_build/lib/pkgconfig" ./configure --prefix="/ffmpeg_build" \
    --pkg-config-flags="--static" --extra-ldexeflags="-static" --extra-libs="-lpthread -lm" --bindir="/bin" --disable-shared --enable-static --enable-gpl --enable-pthreads \
    --enable-libx264 --enable-libsvtav1 --disable-ffplay

RUN make -j

FROM public.ecr.aws/lambda/python:3.12

#COPY --from=builder /gifski/target/release/gifski /usr/local/bin/gifski
#COPY --from=ffmpeg /ffmpeg/ffmpeg-*-static/ffmpeg /usr/local/bin/ffmpeg
#COPY --from=ffmpeg /ffmpeg/ffmpeg-*-static/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg /ffmpeg_sources/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /ffmpeg_sources/ffprobe /usr/local/bin/ffprobe

RUN pip install requests==2.32.3

# Copy function code
COPY __init__.py ${LAMBDA_TASK_ROOT}/app.py

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.lambda_handler" ] 