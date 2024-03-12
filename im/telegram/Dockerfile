# Use the official micromamba image as a base
FROM docker.io/mambaorg/micromamba:1.5-jammy

# Create a new user '$MAMBA_USER' and set the working directory
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.docker.yml /tmp/environment.yml

# Install the specified packages using micromamba
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes    

# TODO
# Force install supabase==2.3.5 --no-deps Conflict with python-telegram-bot = "^20.8"
RUN /opt/conda/bin/pip install supabase==2.3.5
RUN /opt/conda/bin/pip install httpx==0.26.0

USER root
WORKDIR /usr/local/src

# Create a new user 'artisan' and set the working directory
ARG ARTISAN_USER=artisan
ARG ARTISAN_UID=8476
ARG ARTISAN_GID=8476

RUN groupadd --gid $ARTISAN_GID $ARTISAN_USER && \
    useradd --uid $ARTISAN_UID --gid $ARTISAN_GID --shell /bin/bash --create-home $ARTISAN_USER

# Copy the rest of your application files into the Docker image
RUN mkdir -p /artisan/mia
COPY --chown=$ARTISAN_USER:$ARTISAN_USER . /artisan/mia
WORKDIR /artisan/mia

#USER artisan
USER root

# Set environment variables
ENV DOCKER_ENV="docker"

# # Expose the port your FastAPI app will run on
EXPOSE 19003

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set labels
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="emiliabot" \
      org.label-schema.description="telegram bot AI assistant helps deskless managers prioritize tasks, achieve goals, and build lasting habits. Schedule work, analyze routines, and get personalized coaching via voice. " \
      org.label-schema.url="https://artisanlabs.io/" \
      org.label-schema.vcs-url="https://github.com/ArtisanLabs" \
      org.label-schema.maintainer="arpagon@artisanlabs.io" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vendor="ArtisanLabs" \
      org.label-schema.version=$VERSION

# Start the application
CMD ["python", "main.py"]
