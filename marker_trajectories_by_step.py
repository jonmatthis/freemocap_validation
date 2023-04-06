from pathlib import Path
import numpy as np
from freemocap_utils.mediapipe_skeleton_builder import mediapipe_indices
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt


def load_specific_marker_data(marker_data:np.ndarray, joint_to_use:str, axis_to_use:int):
    #for axis to use, 0 = x axis, 1 = y axis, 2 = z axis
    joint_index = mediapipe_indices.index(joint_to_use)
    marker_position_3d = marker_data[:, joint_index, :]
    marker_position_1d = marker_position_3d[:,axis_to_use]
    marker_velocity_1d = np.diff(marker_position_1d, axis = 0)
    marker_velocity_1d = np.append(0,marker_velocity_1d)

    return marker_position_1d, marker_velocity_1d

def detect_zero_crossings(marker_velocity_data:np.ndarray, search_range=2, show_plot = False):
    threshold_to_ignore_next_crossing = 5
    zero_crossings = np.where(np.diff(np.sign(marker_velocity_data)))[0]

    thresholded_zero_crossings_frames = list(zero_crossings.copy())

    for count,frame in enumerate(thresholded_zero_crossings_frames):
        frames_to_filter_out = np.array(range(frame+1,frame+threshold_to_ignore_next_crossing))
        thresholded_zero_crossings_frames = np.setdiff1d(thresholded_zero_crossings_frames,frames_to_filter_out)

    zero_crossings = thresholded_zero_crossings_frames

    heel_strike_frames = []
    toe_off_frames = []

    #searches around the located zero crossing frames to find the frame that has the lowest velocity within the search range
    for frame in zero_crossings:
        start = max(0, frame - search_range)
        end = min(len(marker_velocity_data) - 1, frame + search_range)
        min_abs_velocity_index = start + np.argmin(np.abs(marker_velocity_data[start:end+1]))

        #if the velocity is negative at the original detected frame (which is right before the 0 crossing), then it's toe off (slope is positive)
        if marker_velocity_data[frame] > 0:
            heel_strike_frames.append(min_abs_velocity_index)
        else:
            toe_off_frames.append(min_abs_velocity_index)

    return heel_strike_frames, toe_off_frames

# def divide_3d_data_into_steps(marker_position_3d_data:np.ndarray, event_frames:list):
#     #get the step data for a heel strike/toe off - from the start of the first event to one frame before the next
#     num_frames, num_markers, num_dimensions = marker_position_3d_data.shape
#     dimension_step_dict = {}   
#     for dimension in range(num_dimensions):
#         marker_dict = {}
#         for marker in range(num_markers):
#             step_dict = {}
#             for count,frame in enumerate(range(len(event_frames)-1)):
#                 current_event_frame = int(event_frames[frame])
#                 next_event_frame = int(event_frames[frame+1]) 
#                 step_end_frame = next_event_frame - 1 #end this step right before the next heel strike/toe off
                
#                 step_frame_interval = list(range(current_event_frame,step_end_frame))

#                 if dimension==0:
#                     marker_step_data = marker_position_3d_data[step_frame_interval] - marker_position[step_frame_interval][0] #zero it out in the x direction only 
#                 else:
#                     marker_step_data = marker_position_3d_data[step_frame_interval,marker,dimension]
#                 step_dict[count] = marker_step_data
#             marker_dict[mediapipe_indices[marker]] = step_dict
#         dimension_step_dict[dimension] = marker_dict
    
#     return dimension_step_dict

                
def divide_3d_data_into_steps(marker_position_3d_data: np.ndarray, event_frames: list):
    num_frames, num_markers, num_dimensions = marker_position_3d_data.shape

    def get_marker_step_data(dimension, marker, frame):
        current_event_frame = int(event_frames[frame])
        next_event_frame = int(event_frames[frame + 1])
        step_end_frame = next_event_frame - 1  # end this step right before the next heel strike/toe off
        step_frame_interval = list(range(current_event_frame, step_end_frame))

        marker_step_data = marker_position_3d_data[step_frame_interval, marker, dimension]

        if dimension == 0:
            marker_step_data -= marker_step_data[0]  # zero it out in the x direction only
        
        return marker_step_data

    dimension_step_dict = {
        dimension: {
            mediapipe_indices[marker]: {
                count: get_marker_step_data(dimension, marker, frame)
                for count, frame in enumerate(range(len(event_frames) - 1))
            }
            for marker in range(num_markers)
        }
        for dimension in range(num_dimensions)
    }

    return dimension_step_dict
                


def resample_steps(step_data_dict: dict, num_resampled_points: int):
    resampled_step_dict = {
        dimension: {
            marker: {
                step_num: resample_data(step_data, num_resampled_points=num_resampled_points)
                for step_num, step_data in step_dict.items()
            }
            for marker, step_dict in marker_dict.items()
        }
        for dimension, marker_dict in step_data_dict.items()
    }

    return resampled_step_dict

def resample_data(original_data:np.ndarray,num_resampled_points:int):
    num_current_samples = original_data.shape[0]
    end_time = 10
    original_data_time_array = np.linspace(0,end_time,num_current_samples)
    resampled_data_time_array = np.linspace(0,end_time,num_resampled_points)
    resampled_data = np.empty([resampled_data_time_array.shape[0]])

    interpolation_function = interp1d(original_data_time_array,original_data)
    resampled_data[:] = interpolation_function(resampled_data_time_array)

    return resampled_data

def calculate_step_length_stats(step_data_3d:dict):

    step_stats_dict = {
        dimension:{
            marker: {
                'mean': np.mean(list(step_dict.values()),axis = 0),
                'median': np.median(list(step_dict.values()),axis = 0),
                'std': np.std(list(step_dict.values()),axis = 0) 
            }
            for marker, step_dict in marker_dict.items() 
        }
        for dimension, marker_dict in step_data_3d.items()
    }   

    return step_stats_dict
    
def plot_avg_step_trajectory(step_position_3d:dict, step_stats:dict, marker_to_plot:str, axis_to_plot:int):

    this_joint_step_data = step_position_3d[axis_to_plot][marker_to_plot]
    this_joint_step_stats = step_stats[axis_to_plot][marker_to_plot]

    figure = plt.figure()
    position_ax = figure.add_subplot(111)
    position_ax.set_title(f'{marker_to_plot} Average Step Trajectory')
    position_ax.set_ylabel('X (Forward) Position (mm)')
    position_ax.set_xlabel('Frame #')

    x = np.arange(len(this_joint_step_stats['mean']))

    for step_num in this_joint_step_data.keys():
        position_ax.plot(x,this_joint_step_data[step_num], alpha = .3, color = 'grey')

    position_ax.plot(x,this_joint_step_stats['mean'], color = 'k', label = 'mean')
    position_ax.fill_between(x,this_joint_step_stats['mean']-this_joint_step_stats['std'], this_joint_step_stats['mean'] + this_joint_step_stats['std'], color = 'g', alpha = .2)
    
    position_ax.plot(x,this_joint_step_stats['median'], color = 'k', linestyle ='--', label= 'median')
    position_ax.legend()
    plt.show()


def plot_avg_hip_trajectory(step_stats:dict, axis_to_plot:int):


    left_hip_step_stats = step_stats[axis_to_plot]['left_hip']


    right_hip_step_stats = step_stats[axis_to_plot]['right_hip']

    figure = plt.figure()
    position_ax = figure.add_subplot(111)
    position_ax.set_title(f'Left and Right Hip Average Step Trajectory')
    position_ax.set_ylabel('X (Forward) Position (mm)')
    position_ax.set_xlabel('Frame #')

    x = np.arange(len(left_hip_step_stats['mean']))

    # for step_num in this_joint_step_data.keys():
    #     position_ax.plot(x,this_joint_step_data[step_num], alpha = .3, color = 'grey')

    position_ax.plot(x,left_hip_step_stats['mean'], color = 'g', label = 'left hip mean')
    position_ax.fill_between(x,left_hip_step_stats['mean']-left_hip_step_stats['std'], left_hip_step_stats['mean'] + left_hip_step_stats['std'], color = 'g', alpha = .2)
    
    position_ax.plot(x,right_hip_step_stats['mean'], color = 'b', label = 'right hip mean')
    position_ax.fill_between(x,right_hip_step_stats['mean']-right_hip_step_stats['std'], right_hip_step_stats['mean'] + right_hip_step_stats['std'], color = 'b', alpha = .2)
    
    # position_ax.plot(x,this_joint_step_stats['median'], color = 'k', linestyle ='--', label= 'median')
    
    # position_ax.set_ylim([-100,100])
    position_ax.legend()



    plt.show()


if __name__ == '__main__':
    #path_to_recording_folder = Path(r'C:\Users\Aaron\Documents\freemocap_sessions\recordings')
    path_to_recording_folder = Path(r'C:\Users\aaron\FreeMocap_Data\recording_sessions')


    session_id_list = ['recording_15_19_00_gmt-4__brit_baseline','recording_15_20_51_gmt-4__brit_half_inch', 'recording_15_22_56_gmt-4__brit_one_inch','recording_15_24_58_gmt-4__brit_two_inch']
    label_list = ['baseline', 'half inch lift', 'one inch lift', 'two inch lift']
    
    # session_id_list = ['recording_15_19_00_gmt-4__brit_baseline','recording_15_24_58_gmt-4__brit_two_inch']
    # label_list = ['baseline','two inch lift']

    for session_id, label in zip(session_id_list, label_list):
        path_to_data = path_to_recording_folder/session_id/'output_data'/'mediapipe_body_3d_xyz_transformed.npy'

        marker_data_3d = np.load(path_to_data)
        marker_data_3d[:,:,0] = marker_data_3d[:,:,0]*-1

        marker_position, marker_velocity = load_specific_marker_data(marker_data=marker_data_3d, joint_to_use='left_heel', axis_to_use = 0)
        heel_strike_frames, toe_off_frames = detect_zero_crossings(marker_velocity_data=marker_velocity,search_range=2)

        step_data_3d = divide_3d_data_into_steps(marker_data_3d,heel_strike_frames)
        step_data_left_heel_x = step_data_3d[0]['left_heel']
        resampled_step_data_3d = resample_steps(step_data_dict=step_data_3d, num_resampled_points=100)

        step_stats_dict = calculate_step_length_stats(step_data_3d=resampled_step_data_3d)

        # plot_avg_step_trajectory(step_position_3d=resampled_step_data_3d, step_stats =step_stats_dict, marker_to_plot = 'left_hip', axis_to_plot=0)
        plot_avg_hip_trajectory(step_stats = step_stats_dict, axis_to_plot=2)
    f =2  
