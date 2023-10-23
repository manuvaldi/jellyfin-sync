FROM quay.io/centos/centos:stream9-minimal

RUN microdnf install -y python3.11 python3-pip \
    && microdnf clean all

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "src/sync.py"]
