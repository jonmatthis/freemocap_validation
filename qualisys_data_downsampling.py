from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from freemocap_utils import freemocap_data_loader
from freemocap_utils.mediapipe_skeleton_builder import mediapipe_indices
from scipy import signal
import scipy
from freemocap_utils.skeleton_interpolation import interpolate_freemocap_data

qualisys_indices = [
'head',
'left_ear',
'right_ear',
'cspine',
'left_shoulder',
'right_shoulder',
'left_elbow',
'right_elbow',
'left_wrist',
'right_wrist',
'left_index',
'right_index',
'left_hip',
'right_hip',
'left_knee',
'right_knee',
'left_ankle',
'right_ankle',
'left_heel',
'right_heel',
'left_foot_index',
'right_foot_index',
]

def butter_lowpass_filter(data, cutoff, sampling_rate, order):
    """ Run a low pass butterworth filter on a single column of data"""
    nyquist_freq = 0.5*sampling_rate
    normal_cutoff = cutoff / nyquist_freq
    # Get the filter coefficients 
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    y = signal.filtfilt(b, a, data)
    return y


def filter_skeleton(skeleton_3d_data, cutoff, sampling_rate, order):
    """ Take in a 3d skeleton numpy array and run a low pass butterworth filter on each marker in the data"""
    num_frames = skeleton_3d_data.shape[0]
    num_markers = skeleton_3d_data.shape[1]
    filtered_data = np.empty((num_frames,num_markers,3))

    for marker in range(num_markers):
        for x in range(3):
            filtered_data[:,marker,x] = butter_lowpass_filter(skeleton_3d_data[:,marker,x],cutoff,sampling_rate,order)
    
    return filtered_data


#path_to_qualisys_session_folder = Path(r"D:\ValidationStudy2022\FreeMocap_Data\qualisys_sesh_2022-05-24_16_02_53_JSM_T1_NIH")
path_to_qualisys_session_folder = Path(r"D:\ValidationStudy2022\FreeMocap_Data\qualisys_sesh_2022-05-24_16_02_53_JSM_T1_BOS")
qualisys_data = np.load(path_to_qualisys_session_folder/'DataArrays'/'qualisys_origin_aligned_skeleton_3D.npy')
interpolated_qualisys_data = interpolate_freemocap_data(qualisys_data)

num_samples = interpolated_qualisys_data.shape[0]
num_markers = interpolated_qualisys_data.shape[1]
num_dimensions = interpolated_qualisys_data.shape[2]
q = 10

t_old = np.linspace(0,num_samples*(1/300),num_samples)
t_new = np.linspace(0,num_samples*(1/300),int(num_samples/q))

filtered_qualisys_skeleton = filter_skeleton(interpolated_qualisys_data,6,300,4)

downsampled_qualisys_data = np.empty([int(num_samples/q),num_markers,num_dimensions])

for marker in range (num_markers):
    for dimension in range(num_dimensions):

        interp_function = scipy.interpolate.interp1d(t_old,filtered_qualisys_skeleton[:,marker,dimension])
        downsampled_qualisys_data[:,marker,dimension] = interp_function(t_new)


# interp_function = scipy.interpolate.interp1d(t_old,filtered_qualisys_skeleton[:,5,0])

# qual_resampled = interp_function(t_new)

figure = plt.figure()


trajectories_x_ax = figure.add_subplot(311)
trajectories_y_ax = figure.add_subplot(312)
trajectories_z_ax = figure.add_subplot(313)

trajectories_x_ax.set_ylabel('X Axis (mm)')
trajectories_y_ax.set_ylabel('Y Axis (mm)')
trajectories_z_ax.set_ylabel('Z Axis (mm)')

ax_list = [trajectories_x_ax,trajectories_y_ax,trajectories_z_ax]

for dimension,ax in enumerate(ax_list):
    ax.plot(t_old,qualisys_data[:,5,dimension], color = 'blue', alpha = 1, label = 'original')
    #ax.plot(t_old,interpolated_qualisys_data[:,5,dimension], color = 'red', alpha = 1, label = 'interpolated')
    #ax.plot(t_old,filtered_qualisys_skeleton[:,5,dimension],color = 'red', alpha = .8, label = 'filtered')
    ax.plot(t_new,downsampled_qualisys_data[:,5,dimension], color = 'red', label = 'downsampled')

    ax.legend()

plt.show()


#np.save(path_to_qualisys_session_folder/'DataArrays'/'downsampled_qualisys_3D.npy',downsampled_qualisys_data)


f = 2
# ### OLD
# time_series = np.linspace(0,300,num_samples)
# samples_decimated = int(num_samples/q)

# downsampled_qualisys_data = np.empty([samples_decimated+1,num_markers,num_dimensions])
# resampled_qualisys_data = np.empty([samples_decimated+1,num_markers,num_dimensions])
# poly_qualisys_data = np.empty([samples_decimated+1,num_markers,num_dimensions])

# for marker in range (num_markers):
#     for dimension in range(num_dimensions):
#         downsampled_qualisys_data[:,marker,dimension] = signal.decimate(interpolated_qualisys_data[:,marker,dimension],q,  ftype='fir')
#         resampled_qualisys_data[:,marker,dimension] = signal.resample(interpolated_qualisys_data[:,marker,dimension],samples_decimated+1)
#         poly_qualisys_data[:,marker,dimension] = signal.resample_poly(interpolated_qualisys_data[:,marker,dimension],10,100)
# downsampled_time_series = signal.decimate(time_series,q)


# figure = plt.figure()


# trajectories_x_ax = figure.add_subplot(311)
# trajectories_y_ax = figure.add_subplot(312)
# trajectories_z_ax = figure.add_subplot(313)

# ax_list = [trajectories_x_ax,trajectories_y_ax,trajectories_z_ax]

# for dimension,ax in enumerate(ax_list):
#     ax.plot(time_series,qualisys_data[:,5,dimension], color = 'blue', alpha = .8, label = 'original')
#     #ax.plot(time_series,interpolated_qualisys_data[:,5,dimension], color = 'yellow', alpha = .8, label = 'interpolated')
#     ax.plot(downsampled_time_series,downsampled_qualisys_data[:,5,dimension], color = 'purple', alpha = .5, label = 'scipy decimate')
#     ax.plot(downsampled_time_series,resampled_qualisys_data[:,5,dimension],color = 'red', alpha = .3, label = 'scipy resample')
#     ax.plot(downsampled_time_series,poly_qualisys_data[:,5,dimension],color = 'red', alpha = .3, label = 'scipy poly')
#     ax.legend()



# plt.show()
# #np.save(path_to_qualysis_session_folder/'DataArrays'/'downsampled_qualisys_3D.npy',downsampled_qualisys_data)

# f = 2 