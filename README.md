# SpokenStreamSleuth
Your go-to solution for effortlessly detecting, analyzing, and labelling spoken audio streams within your Plex media library. 

### The Problem
Unlabelled media. At a minimum it frustrates the completionist, and at it's worst it is inaccessible and confusing to those who rely on the comfort of entertainment as an escape. If we're looking to curate a specific composition it's difficult to asses your progress without langauge tags on the audio streams contained therein. 

### The Solution
Retrieve a list of unknown audio streams and query Whisper for their language. Systematically update the metadata of the original file and then notify Plex that an analysis is needed.
### Features
*  Automated language identification
*  Fixes the files that are supported, skips those that aren't
*  Edits the source file itself so the solution is evident no matter what is accessing the video

## Installation
If I can do it, so can you!
### Prerequisites
*  Python3.x
*  FFmpeg
*  mkvtoolnix
*  [ahmetoner/whisper-asr-webservice](https://github.com/ahmetoner/whisper-asr-webservice)

### Steps (Using a [tteck](https://tteck.github.io/Proxmox/) Ubuntu/Debian installion as an example)
1. Install prerequisites
```console
sudo apt update && sudo apt install git ffmpeg mkvtoolnix pip
```
2. Clone the repository and enter it
```console
git clone https://github.com/MrSaiclops/SpokenStreamSleuth && cd SpokenStreamSleuth
```
3. Install Python requirements
```console
pip install -r requirements.txt
```

4. Run Whisper webservice
```console
docker run -d -p 9000:9000 -e ASR_MODEL=medium -e ASR_ENGINE=faster_whisper onerahmet/openai-whisper-asr-webservice:latest
```
5. Set config settings
   
   ``nano config.txt``

   Instructions for getting the token [here](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/#toc-0). If whisper is hosted on the same machine you should be fine to use ``localhost:9000``
```console
plexURL=http://192.168.1.237:32400
token=TGsM67-BJBatyVYchvmy
library=TV Shows
whisper=192.168.1.222:9000
```

