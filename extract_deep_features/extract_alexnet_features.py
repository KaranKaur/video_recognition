import imageio
import numpy as np
import os
import pickle
from pandas import read_csv, DataFrame
from scipy.misc.pilutil import imresize

import torch
import torch.nn as nn
from torchvision import models
from torch.autograd import Variable

CATEGORIES = ["boxing", "handclapping", "handwaving", "jogging", "running", "walking"]
DATASET_DIR = "../../data"

TRAIN_PEOPLE_ID = [11, 12, 13, 14, 15, 16, 17, 18]
DEV_PEOPLE_ID = [19, 20, 21, 23, 24, 25, 1, 4]
TEST_PEOPLE_ID = [22, 2, 3, 5, 6, 7, 8, 9, 10]

def get_human_frames(ex ,dataframe):

    Name = dataframe.columns.get_loc("Filename")
    start_1 =  dataframe.columns.get_loc("start_1")
    end_1 =  dataframe.columns.get_loc("end_1")
    start_2 =  dataframe.columns.get_loc("start_2")
    end_2 =  dataframe.columns.get_loc("end_2")
    start_3 =  dataframe.columns.get_loc("start_3")
    end_3 =  dataframe.columns.get_loc("end_3")
    start_4 =  dataframe.columns.get_loc("start_4")
    end_4 =  dataframe.columns.get_loc("end_4")
    FramesOFIntrest = dataframe.values
    frames = []

    for i in range(FramesOFIntrest.shape[0]):
        
        if(FramesOFIntrest[i,Name] in ex["filename"] ):

            if(not (np.isnan(FramesOFIntrest[i,start_1])  or np.isnan(FramesOFIntrest[i,end_1]))):
                n = int(FramesOFIntrest[i,start_1]-1) 
                while n<int(FramesOFIntrest[i,end_1]) :
                        frames.append(ex["frames"][n])
                        n+=1
                    
            if(not (np.isnan(FramesOFIntrest[i,start_2])  or np.isnan(FramesOFIntrest[i,end_2]))):
                n = int(FramesOFIntrest[i,start_2]-1) 
                while n<int(FramesOFIntrest[i,end_2]) :
                        frames.append(ex["frames"][n])
                        n+=1
            if(not (np.isnan(FramesOFIntrest[i,start_3])  or np.isnan(FramesOFIntrest[i,end_3]))):
                n = int(FramesOFIntrest[i,start_3]-1) 
                while n<int(FramesOFIntrest[i,end_3]) :
                        frames.append(ex["frames"][n])
                        n+=1
            if(not (np.isnan(FramesOFIntrest[i,start_4])  or np.isnan(FramesOFIntrest[i,end_4]))):
                n = int(FramesOFIntrest[i,start_4]-1) 
                while n<int(FramesOFIntrest[i,end_4] ) and n<len(ex["frames"]):
                        frames.append(ex["frames"][n])
                        n+=1

    return frames

def preprocess(frame):
    # Necessary preprocess step if we use pretrained models
    # of PyTorch.
    frame /= 255.0
    frame -= np.array([0.485, 0.456, 0.406], dtype=np.float32)
    frame /= np.array([0.229, 0.224, 0.225], dtype=np.float32)
    return frame

if __name__ == "__main__":
    FramesOFIntrest = os.path.join(DATASET_DIR, "FramesOfIntrest.csv")
    FramesOFIntrest_df  = read_csv(FramesOFIntrest, names=None)

    model = models.alexnet(pretrained=True)
    # remove last fully-connected layer
    new_classifier = nn.Sequential(*list(model.classifier.children())[:-1])
    model.classifier = new_classifier

    train_set = []
    dev_set = []
    test_set = []

    num_vids = 0
    for category in CATEGORIES:
        print("Processing category %s" % category)

        folder_path = os.path.join("..", "..", "data", category)
        filenames = os.listdir(folder_path)

        for filename in filenames:
            filepath = os.path.join("..", "..", "data", category, filename)
            vid = imageio.get_reader(filepath, "ffmpeg")

            frames = []
            for i, frame in enumerate(vid):
                frame = imresize(frame, (224, 224))
                frame = frame.astype(np.float32)
                frames.append(frame)

            ex = {
                "filename": filename,
                "frames": frames
            }
            frames = get_human_frames(ex, FramesOFIntrest_df)
            
            deep_feats = []
            for frame in frames:
                frame = preprocess(frame)

                # Put channel first.
                frame = np.transpose(frame, (2, 0, 1))

                # PyTorch wants channel first.
                frame = frame.reshape((1, 3, 224, 224))

                tensor = torch.from_numpy(frame)
                vari = Variable(tensor)
                deep_feat = model(vari).data[0].numpy()
                # print(deep_feat)
                # print(deep_feat.shape)
                # print(np.sum(deep_feat))
                # print(np.count_nonzero(deep_feat))

                deep_feats.append(deep_feat)

            item = {
                "category": category,
                "filename": filename,
                "frames": deep_feats
            }

            person_id = int(filename.split("_")[0][6:])
            if person_id in TRAIN_PEOPLE_ID:
                train_set.append(item)
            elif person_id in DEV_PEOPLE_ID:
                dev_set.append(item)
            else:
                test_set.append(item)
            
            num_vids += 1
            print("Processed %d videos" % num_vids)


    pickle.dump(train_set, open(os.path.join(DATASET_DIR, "train_alexnet.pickle"), "wb"))
    pickle.dump(dev_set, open(os.path.join(DATASET_DIR, "dev_alexnet.pickle"), "wb"))
    pickle.dump(test_set, open(os.path.join(DATASET_DIR, "test_alexnet.pickle"), "wb"))

