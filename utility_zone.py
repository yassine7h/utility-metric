import numpy as np
import pandas as pd

def main(anon, org, params, nb_orig_lines):
    
    use_zone_dim = False
    zone_size=[0.0,0.0]
    matrix_size=[0,0]
    neighbors_coefficient=params["neighbors_coefficient"]
    
    if "zone_size" in params:
        zone_size=params["zone_size"]
        use_zone_dim=True
    else:
        matrix_size=params["matrix_size"]
        
    #rename anonymous ids
    for i in pd.unique(org["id"]):
        anon.loc[org[org.id==i].index,"id"]=i
    
    ids_list=org["id"].unique().tolist()
    score_total=0

    for id_i in ids_list:
        
        df_org_projection=org[(org["id"]==id_i)]
        df_anon_projection=anon[(anon["id"]==id_i)]
        
        min_longitude=min(df_org_projection["longitude"])
        max_longitude=max(df_org_projection["longitude"])
        min_latitude=min(df_org_projection["latitude"])
        max_latitude=max(df_org_projection["latitude"])
        
        if use_zone_dim:           
            n=int((max_longitude-min_longitude)/zone_size[0])+1
            m=int((max_latitude-min_latitude)/zone_size[1])+1
            matrix_size=[n,m]
        
        matrix_org=np.zeros((matrix_size[0],matrix_size[1]),dtype=int)
        matrix_anon=np.zeros((matrix_size[0],matrix_size[1]),dtype=int)
        
        longitude_int_len=(max_longitude-min_longitude)/float(matrix_size[0])
        latitude_int_len=(max_latitude-min_latitude)/float(matrix_size[1])
        
        def calc_long_idx(long):
            idx=int((long-min_longitude)/longitude_int_len)
            if idx < 0 or idx > matrix_size[0]:
                return None
            elif idx==matrix_size[0]:
                return matrix_size[0]-1
            else: return idx
            
        def calc_lat_idx(lat):
            idx=int((lat-min_latitude)/latitude_int_len)
            if idx < 0:
                return 0
            elif idx>=matrix_size[1]:
                return matrix_size[1]-1
            else: return idx
        
        def insert_position(_row,_matrix):
            _longitude_idx=calc_long_idx(_row["longitude"])
            _latitude_idx=calc_lat_idx(_row["latitude"])
            if _longitude_idx is not None and _latitude_idx is not None:
                _matrix[_longitude_idx][_latitude_idx]+=1
                
        df_org_projection[["longitude","latitude"]].apply(lambda x:insert_position(x,matrix_org),axis=1)
        df_anon_projection[["longitude","latitude"]].apply(lambda x:insert_position(x,matrix_anon),axis=1)
        
        partial_score=calc_score(matrix_org,matrix_anon,neighbors_coefficient)
        score_total+=partial_score/float(len(ids_list))
        
        print("ID ["+str(id_i)+"] score -> "+str(partial_score))

    return score_total
        
def calc_score(_matrix_org, _matrix_anon,_neighbors_coefficient):
    rows, cols = _matrix_org.shape
    def get_neighbors(np_arr, _i, _j):
        neighbors = 0
        if _i > 0:
            neighbors+=(np_arr[_i - 1, _j])
        if _i < rows - 1:
            neighbors+=(np_arr[_i + 1, _j])
        if _j > 0:
            neighbors+=(np_arr[_i, _j - 1])
        if _j < cols - 1:
            neighbors+=(np_arr[_i, _j + 1])
        if _i > 0 and _j > 0:
            neighbors+=(np_arr[_i - 1, _j - 1])
        if _i > 0 and _j < cols - 1:
            neighbors+=(np_arr[_i - 1, _j + 1])
        if _i < rows - 1 and _j > 0:
            neighbors+=(np_arr[_i + 1, _j - 1])
        if _i < rows - 1 and _j < cols - 1:
            neighbors+=(np_arr[_i + 1, _j + 1])
        return neighbors
    def calc_zone_score(cel_org,cel):
        if cel_org==cel :
            return 1
        return  0 if cel >= cel_org * 2 or cel == 0 else 1-abs(cel_org-cel)/cel_org
    _score_total=0
    for i in range(0,rows):
        for j in range(0,cols):
            zone_score = calc_zone_score(_matrix_org[i][j], _matrix_anon[i][j])
            neighbors_score=calc_zone_score(get_neighbors(_matrix_org, i, j) + _matrix_org[i][j],
                                            get_neighbors(_matrix_anon, i, j) + _matrix_anon[i][j])
            _score_total+= (zone_score * 1-_neighbors_coefficient + neighbors_score * _neighbors_coefficient) 
    return _score_total/(rows * cols)
    



##################################################################################################
################ test #########################################################################

_org=pd.read_csv("ORIGINAL.csv",delimiter = '\t',names=["id", "date", "longitude", "latitude"])
_anon=pd.read_csv("ANON.csv",delimiter = '\t',names=["id", "date", "longitude", "latitude"])

org=_org.copy()
anon=_anon.copy()
anon = anon.loc[anon['id'] != "DEL"]
org = org.loc[anon.index]


my_params={
    #"matrix_size":[10,10],
    "neighbors_coefficient":0.4,
    "zone_size":[0.05,0.05],
}
       
my_score=main(anon,org,my_params,0)
print("Total score -> "+str(my_score))
