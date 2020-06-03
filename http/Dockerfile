FROM radonconsortium/radon-ctt-agent:base

WORKDIR /opt

ENV PLUGIN_NAME http
ENV PLUGIN_PATH /opt/$CTT_AGENT_NAME/plugins/$PLUGIN_NAME
RUN mkdir -p $PLUGIN_PATH
COPY . $PLUGIN_PATH
