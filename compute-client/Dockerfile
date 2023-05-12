FROM debian:11

WORKDIR /

ENV PORT=44372
ENV SERVER=localhost
RUN apt update && apt install -y libtinfo-dev libgmp-dev zlib1g-dev python pip wget gnuplot ffmpeg imagemagick
RUN python3 -m pip install --upgrade pip
RUN wget https://futhark-lang.org/releases/futhark-nightly-linux-x86_64.tar.xz
RUN tar xvf futhark-nightly-linux-x86_64.tar.xz
RUN cd futhark-nightly-linux-x86_64 && make install
COPY . .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

CMD python --version
CMD ./compute-client.py --port=${PORT} --address=${SERVER}
