FROM public.ecr.aws/lambda/python:3.14
RUN dnf -y update
RUN dnf -y install git && dnf clean all
RUN dnf -y install tar gzip zlib freetype-devel \
    gcc \
    ghostscript \
    lcms2-devel \
    libffi-devel \
    libimagequant-devel \
    libjpeg-devel \
    libraqm-devel \
    libtiff-devel \
    libwebp-devel \
    make \
    openjpeg2-devel \
    sudo \
    tcl-devel \
    tk-devel \
    which \
    xorg-x11-server-Xvfb \
    zlib-devel \
    && dnf clean all
RUN pip install -U --force-reinstall pillow-simd
RUN pip install requests

# Copy function code
COPY __init__.py ${LAMBDA_TASK_ROOT}/app.py
COPY 500.jpg ${LAMBDA_TASK_ROOT}/500.jpg

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.lambda_handler" ] 