# E:\Trino_Table\docker\Dockerfile
# docker\Dockerfile
FROM bitnami/spark:3.4.1

USER root

# Install Python & dependencies
RUN pip install pyspark==3.4.1 kafka-python

# Prepare folders
RUN mkdir -p /app/scripts /app/configs /opt/extra_jars

# Copy configs & JARs if needed
COPY configs/ /app/configs/
COPY jars/*.jar /opt/extra_jars/

# Correct permissions
RUN chown -R 1001:1001 /app /opt/extra_jars

USER 1001
WORKDIR /app
