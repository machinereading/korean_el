# ISWC 2019 EL Model

## Introduction

Based on model of [Improving Entity Linking by 
Modeling Latent Relations between Mentions](https://arxiv.org/pdf/1804.10637.pdf). ACL 2018. 
<https://github.com/lephong/mulrel-nel> 

### Environment

virtual or conda environment with python 3.6 is recommended

execute `pip3 install -r requirements.txt`

#### Data Format

For train and test, you need specific data format.
Train(or test) file is a single list. Each of element is a python dictionary, which is:
	"text": Original text of sentence
	"entities": List of dict
	"fileName": Optional. If empty, the system will give temporary file name.

Each entity is composed of:
	"start": Start character index of entity.
	"end": End character index of entity.
	"dataType": Optional. Data type given from NER module
	"surface": Surface form of entity. This must be same with text[start:end].
	"entity": Entity that should be matched. In evaluation mode, this will role as answer. In test mode, this will be predicted output.

We provide our corpus at corpus/ directory as reference.

#### Additional Data

To run, you need several additional data. You can acquire them at 


#### Train

Before training, make sure you created data/el/ directory and downloaded all required data.
For train, you have to make data files(cs_train.conll, cs_train.tsv) with the same format of test or dev files in the same directory.
To train a 3-relation ment-norm model, from the main folder run 

    python3 train.py [MODEL_NAME]
 
Using a GTX 1080 Ti GPU it will take about 1 hour. The output is a model saved in two files: 
`[MODEL_NAME].config` and `[MODEL_NAME].state_dict`, which are saved at data/el/ directory.

#### Evaluation

Execute

    python3 eval.py [MODEL_NAME]

## Licenses
* `CC BY-NC-SA` [Attribution-NonCommercial-ShareAlike](https://creativecommons.org/licenses/by-nc-sa/2.0/)
* If you want to commercialize this resource, [please contact to us](http://mrlab.kaist.ac.kr/contact)

## Publisher
[Machine Reading Lab](http://mrlab.kaist.ac.kr/) @ KAIST

## Acknowledgement
This work was supported by Institute for Information & communications Technology Promotion(IITP) grant funded by the Korea government(MSIT) (2013-0-00109, WiseKB: Big data based self-evolving knowledge base and reasoning platform)