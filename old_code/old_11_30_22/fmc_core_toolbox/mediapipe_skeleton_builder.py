from rich.progress import track 

mediapipe_indices = [
    'nose',
    'left_eye_inner',
    'left_eye',
    'left_eye_outer',
    'right_eye_inner',
    'right_eye',
    'right_eye_outer',
    'left_ear',
    'right_ear',
    'mouth_left',
    'mouth_right',
    'left_shoulder',
    'right_shoulder',
    'left_elbow',
    'right_elbow',
    'left_wrist',
    'right_wrist',
    'left_pinky',
    'right_pinky',
    'left_index',
    'right_index',
    'left_thumb',
    'right_thumb',
    'left_hip',
    'right_hip',
    'left_knee',
    'right_knee',
    'left_ankle',
    'right_ankle',
    'left_heel',
    'right_heel',
    'left_foot_index',
    'right_foot_index'
    ]
    
def slice_mediapipe_data(mediapipe_full_skeleton_data, num_pose_joints):
    pose_joint_range = range(num_pose_joints)

    mediapipe_pose_data = mediapipe_full_skeleton_data[:,0:num_pose_joints,:] #load just the pose joints into a data array, removing hands and face data 

    return mediapipe_pose_data


def return_indices_of_joints(list_of_indices, list_of_joint_names):

    indices = []
    for name in list_of_joint_names:
        this_name_index = list_of_indices.index(name)
        indices.append(this_name_index)
    
    return indices

def return_XYZ_coordinates_of_markers(freemocap_data, indices_list,frame):

        XYZ_coordinates = []
        for index in indices_list:
            this_joint_coordinate = freemocap_data[frame,index,:]
            XYZ_coordinates.append(this_joint_coordinate)

        return XYZ_coordinates

    
def build_virtual_trunk_marker(freemocap_data,list_of_indices, trunk_joint_connection,frame):
        trunk_marker_indices = return_indices_of_joints(list_of_indices, trunk_joint_connection)

        trunk_XYZ_coordinates = return_XYZ_coordinates_of_markers(freemocap_data,trunk_marker_indices,frame)

        trunk_proximal = (trunk_XYZ_coordinates[0] + trunk_XYZ_coordinates[1])/2
        trunk_distal = (trunk_XYZ_coordinates[2] + trunk_XYZ_coordinates[3])/2

        return trunk_proximal, trunk_distal


    
 

def build_mediapipe_skeleton(mediapipe_pose_data,segment_dataframe, mediapipe_indices) -> list:
    """ This function takes in the mediapipe pose data array and the segment_conn_len_perc_dataframe. 
        For each frame of data, it loops through each segment we want to find and identifies the names
        of the proximal and distal joints of that segment. Then it searches the mediapipe_indices list
        to find the index that corresponds to the name of that segment. We plug the index into the 
        mediapipe_pose_data array to find the proximal/distal joints' XYZ coordinates at that frame. 
        The segment, its proximal joint and its distal joint gets thrown into a dictionary. 
        And then that dictionary gets saved to a list for each frame. By the end of the function, you 
        have a list that contains the skeleton segment XYZ coordinates for each frame."""


    num_frames = mediapipe_pose_data.shape[0]
    num_frame_range = range(num_frames)

    mediapipe_frame_segment_joint_XYZ = [] #empty list to hold all the skeleton XYZ coordinates/frame

    
    for frame in track(num_frame_range, description= 'Building a MediaPipe Skeleton'): 

        trunk_joint_connection = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
        trunk_virtual_markers = build_virtual_trunk_marker(mediapipe_pose_data, mediapipe_indices, trunk_joint_connection,frame)    

        mediapipe_pose_skeleton_coordinates = {}
        for segment,segment_info in segment_dataframe.iterrows(): #iterate through the data frame by the segment name and all the info for that segment
            if segment == 'trunk':

                #based on index, excract coordinate data from fmc mediapipe data
                mediapipe_pose_skeleton_coordinates[segment] = [trunk_virtual_markers[0], 
                                                                trunk_virtual_markers[1]
                                                                ]
            elif segment == 'left_hand' or segment == 'right_hand':
                proximal_joint_hand = segment_info['Joint_Connection'][0]
                if segment == 'left_hand':
                    distal_joint_hand = 'left_index'
                else:
                    distal_joint_hand = 'right_index'

                proximal_joint_hand_index = mediapipe_indices.index(proximal_joint_hand)
                distal_joint_hand_index = mediapipe_indices.index(distal_joint_hand)

                mediapipe_pose_skeleton_coordinates[segment] = [mediapipe_pose_data[frame,proximal_joint_hand_index, :],
                                                                mediapipe_pose_data[frame,distal_joint_hand_index,:]]

            elif segment == 'left_foot' or segment == 'right_foot':
                if segment == 'left_foot':
                    proximal_joint_foot_name = 'left_ankle'
                else:
                    proximal_joint_foot_name = 'right_ankle'
                
                proximal_joint_foot_index = mediapipe_indices.index(proximal_joint_foot_name)

                distal_joint_foot = segment_info['Joint_Connection'][1]
                distal_joint_foot_index = mediapipe_indices.index(distal_joint_foot)
                mediapipe_pose_skeleton_coordinates[segment] = [mediapipe_pose_data[frame,proximal_joint_foot_index, :],
                                                                mediapipe_pose_data[frame, distal_joint_foot_index,:]]            

            else:
                proximal_joint_name = segment_info['Joint_Connection'][0] 
                distal_joint_name = segment_info['Joint_Connection'][1]

            #get the mediapipe index for the proximal and distal joint for this segment
                proximal_joint_index = mediapipe_indices.index(proximal_joint_name)
                distal_joint_index = mediapipe_indices.index(distal_joint_name)

            #use the mediapipe indices to get the XYZ coordinates for the prox/distal joints and throw it in a dictionary
            #mediapipe_pose_skeleton_coordinates[segment] = {'proximal':mediapipe_pose_data[frame,proximal_joint_index,:],'distal':mediapipe_pose_data[frame,distal_joint_index,:]}
                mediapipe_pose_skeleton_coordinates[segment] = [mediapipe_pose_data[frame,proximal_joint_index,:],mediapipe_pose_data[frame,distal_joint_index,:]]
                
        mediapipe_frame_segment_joint_XYZ.append(mediapipe_pose_skeleton_coordinates)
        f = 2 
    
    return mediapipe_frame_segment_joint_XYZ