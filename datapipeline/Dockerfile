FROM radonconsortium/radon-ctt-agent:base

WORKDIR /opt

ENV PLUGIN_NAME datapipeline
ENV PLUGIN_PATH "$PLUGIN_DIR/$PLUGIN_NAME"

RUN mkdir -p "$PLUGIN_PATH"

COPY . "$PLUGIN_PATH"

