import pandas as pd
import numpy as np
import time
from utils import *


class FAA_Parser(object):

    def __init__(self, call_sign, time, chunk_size):

        self.time = time
        self.call_sign = call_sign
        self.chunk_size = chunk_size

        # specific row numbers to keep
        self.rows = []

        # specific colomn numbers to keep
        # cols = [0, 1, 7, 17]  # flightID, time, flight number, flight plan
        self.cols = [0, 1, 7, 9, 10, 11, 17]  # include lat and lon

        # track point is the array to store trajectories
        # self.track_point = []

    def count_rows(self):

        t0 = time.time()
        n = sum(1 for line in open('data/IFF_USA_' + self.time + '_050000_86396.csv'))
        print "loaded " + str(n) + " rows of data"
        print('Elapsed time : ', time.time() - t0)

    def get_flight_plan(self):

        # chunk number index
        i = 0

        df = pd.read_csv('data/IFF_USA_' + self.time + '_050000_86396.csv', chunksize=self.chunk_size, iterator=True,
                         names=range(0, 18), low_memory=False)

        flight_plan_change_time = []
        flight_plan_change = []
        track_point = np.empty((0, 4))

        for chunk in df:

            i = i + 1
            print "reading chunk number " + str(i)

            # self.rows.extend(chunk.index[chunk[7] == self.call_sign])
            # if self.rows.__len__() != 0:
            #     self.rows = np.asarray(self.rows) - self.chunk_size * (i - 1)
            # self.rows = list(self.rows)
            self.rows = []
            self.rows.extend(chunk.index[chunk[7] == self.call_sign])

            # restore the data from dataframe
            data = chunk.ix[self.rows][self.cols]

            # clear ? and nan values in the dataframe
            data = data.replace({'?': np.nan}).dropna()

            # divide data into flight plan and track point
            track_point_chunk = np.asarray(data[data[0] == 3])
            flight_plan_chunk = data[data[0] == 4]

            # flight_plan = list(set(flight_plan[17]))  # remove duplicate in flight plan
            fp, fp_indices = np.unique(flight_plan_chunk[17], return_index=True)
            fp_indices = np.sort(fp_indices)

            flight_plan_chunk = flight_plan_chunk.values[fp_indices]
            flight_plan_change_time_chunk = flight_plan_chunk[:, 1]
            flight_plan_change_chunk = flight_plan_chunk[:, -1]

            track_point_chunk = np.delete(track_point_chunk, [0, 2, 6], axis=1)  # col1:unix time, col2:lon, col3:lat
            track_point_chunk[:, [1, 2]] = track_point_chunk[:, [2, 1]]  # swap last two colomns

            if flight_plan_change_chunk.size != 0:
                flight_plan_change.append(flight_plan_change_chunk)
                flight_plan_change_time.append(flight_plan_change_time_chunk)
                track_point = np.concatenate((track_point, track_point_chunk), axis=0)

        return flight_plan_change_time, flight_plan_change, track_point


if __name__ == '__main__':  # main function only for testing purpose

    call_sign = 'ACA759'
    time = '20170406'
    chunk_size = 1e6

    fun = FAA_Parser(call_sign, time, chunk_size)
    flight_plan_sequence_change_time, flight_plan_change_sequence, trajectory = fun.get_flight_plan()
    save_csv(trajectory, call_sign, time)
    save_trx(flight_plan_change_sequence, call_sign, time)  # save trx files