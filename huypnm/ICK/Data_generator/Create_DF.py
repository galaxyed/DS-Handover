import pandas as pd
import numpy as np
import os
from datetime import datetime, date
from tqdm import tqdm

tqdm.pandas()

if os.name =='nt':
    df_path = r"D:\Coding_pratice\_Data\GalaxyEducation\ICK"
else:
    df_path = '/Users/admin/_Work/Data/icanKID'

# df_User = pd.read_csv(
#     os.path.join(df_path,'df_User.csv')
#     )
df_User = pd.read_csv(
    os.path.join(df_path,'df_User_Child_DeviceBrand.csv')
    )
df_Engagement = pd.read_csv(
    os.path.join(df_path, 'df_Engagement.csv')
    )
df_Engagement_updated = pd.read_csv(
os.path.join(df_path, 'df_Engagement_updated.csv')
    )
df_Payment = pd.read_csv(
    os.path.join(df_path, 'df_Payment.csv')
    )
df_fake_user = pd.read_csv(
    os.path.join(df_path, 'df_fake_paid_users.csv')
    )

# Discard fake user
df_User = df_User[~df_User['UserID'].isin(df_fake_user['UserID'])]
df_Engagement = df_Engagement[~df_Engagement['UserID'].isin(df_fake_user['UserID'])]
df_Payment = df_Payment[~df_Payment['UserID'].isin(df_fake_user['UserID'])]

# Get user's Age
df_User['monthBday'] = pd.to_datetime(df_User.ChildBday).dt.month
df_User['Age'] = (pd.to_datetime(date.today()) - pd.to_datetime(df_User.ChildBday)).astype('<m8[Y]').astype('int')

def day_of_week_func(x):
    """
        Input: Normal date

        Return: Day in week
    """
    # Why don't need .dt if apply to Series
    # https://stackoverflow.com/questions/62803633/timestamp-object-has-no-attribute-dt#_=_
    x = pd.to_datetime(x).dayofweek
    day_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dict_dayofweek = {i:v for i,v in enumerate(day_of_week)}

    return dict_dayofweek[x]

def slope_function(x, y):
    # x: Timeseries
    # y: Datapoint
    n = len(x)
    x_sum = np.sum(x)
    y_sum = np.sum(y)
    xy_sum = np.sum(x*y)
    x2_sum = np.sum(x**2)

    denominator = n * x2_sum - x_sum**2
    if denominator == 0:
        return 0
    
    else:
        return (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum**2)

def slope_function_2(x, y):
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    sx = np.std(x, ddof=1)
    sy = np.std(y, ddof=1)
    denominator = (len(x) * sx * sy)

    if denominator == 0:
        return 0
    else:
        r = np.sum((x - x_mean) * (y - y_mean)) / (len(x) * sx * sy)
        m = r * (sy / sx)
        return m

def accumulate_func(Series_values:pd.Series, take_abs:int):
    if take_abs:
        accumulate = lambda x,y: np.abs(x-y)
    else:
        accumulate = lambda x,y: x-y

    return ([
        accumulate(Series_values.iloc[i], Series_values.iloc[i-1]) for i in range(1, len(Series_values))
        ] if len(Series_values) > 1 else [0])

def interest_rate(Engagement, userID):
    usedDay_column = 'usedDays'
    if usedDay_column in Engagement.columns:
        pass
    else:
        usedDay_column = 'nth_day_from_registration'

    temp = Engagement[Engagement.UserID == userID].sort_values(by=usedDay_column)
    UserID_df = temp[['UserID']].head(1).reset_index(drop=True)
    temp['interest'] = temp['UsageTime'] * temp['Records']

    temp_check = temp.groupby('ActionType')['interest'].agg(
        total_interest=lambda x: sum(x),
        average_interest=lambda x: np.mean(x),
        # accumulate_inc_avg=lambda x: np.mean([
        #     x.iloc[i] - x.iloc[i-1] if (i != 0) and (x.iloc[i] - x.iloc[i-1]) > 0 else 0 for i in range(1, len(x))]),
        # accumulate_dec=lambda x: sum([
        #     x.iloc[i] - x.iloc[i-1] if (i != 0) and (x.iloc[i] - x.iloc[i-1]) < 0 else 0 for i in range(len(x))]),
        # total_accumulate_avg=lambda x: np.mean(accumulate_func(x, True)),
        accumulate=lambda x: np.sum(accumulate_func(x, False)),

    ).reset_index()

    grouped = temp.groupby('ActionType')
    # temp_check_2 = grouped.agg(
    #     Slope=pd.NamedAgg(
    #         column='interest', 
    #         aggfunc=lambda x: slope_function(
    #             grouped[usedDay_column].get_group(x.name),
    #             x       
    # ))).reset_index()

    temp_check_3 = grouped.agg(
        Slope_2=pd.NamedAgg(
            column='interest', 
            aggfunc=lambda x: slope_function_2(
                grouped[usedDay_column].get_group(x.name),
                x       
    ))).reset_index()

    # temp_check = pd.merge(temp_check, temp_check_2, on='ActionType')
    temp_check = pd.merge(temp_check, temp_check_3, on='ActionType')

    # To tell if the recent activity increase or decrease throughout the span of 't' days
    # Value range between [-1,1], with 0 as no trend (only 1 day of active)
    temp_check.reset_index(inplace=True, drop=True)
    temp_check['Slope_norm'] = temp_check['Slope_2'] / temp_check['average_interest']
    # display(temp_check)

    temp_check.drop(
        columns=['Slope_2'], 
        inplace=True)

    most_active = temp_check.iloc[[temp_check['total_interest'].idxmax()]].reset_index(drop=True)
    most_accumulate = temp_check.iloc[[temp_check['accumulate'].idxmax()]].reset_index(drop=True)
    
    most_active.fillna(0, inplace=True)
    most_active.drop(columns=['accumulate','average_interest'], inplace=True)
    most_accumulate.fillna(0, inplace=True)
    most_accumulate.drop(columns=['total_interest', 'average_interest'], inplace=True)

    most_active.rename(columns={
        "ActionType": "MostInterest",
        "total_interest": "TotalInterestRatio",
        "Slope_norm": "InterestTrend"
    },inplace=True)

    most_accumulate.rename(columns={
        "ActionType": "MostAccumulate",
        "accumulate": "TotalAccuRatio",
        "Slope_norm": "AccuTrend"
    }, inplace=True)
    total_interest = temp_check['total_interest'].sum()
    total_accumulate = np.sum(np.abs(temp_check['accumulate']))

    if total_interest == 0:
        most_active['TotalInterestRatio'] = 0
    else:
        most_active['TotalInterestRatio'] = most_active['TotalInterestRatio'] / total_interest
    
    if total_accumulate == 0:
        most_accumulate['TotalAccuRatio'] = 0
    else:
        most_accumulate['TotalAccuRatio'] = most_accumulate['TotalAccuRatio'] / total_accumulate
   
    return pd.concat([UserID_df, most_active, most_accumulate], axis=1)


def create_dataframe(dataframes):
    df_User, df_Engagement, df_Payment = dataframes

    # Rebrand rarely used brand
    rep_brand = df_User['DeviceBrand'].value_counts()[
    df_User['DeviceBrand'].value_counts() < df_User['DeviceBrand'].value_counts().mean()].index.values
    df_User['DeviceBrand'] = df_User['DeviceBrand'].apply(lambda x: 'Other brand' if x in rep_brand else x)

    device_brand_df = pd.get_dummies(
            df_User[['UserID', 'DeviceBrand']],
            columns=['DeviceBrand'], prefix= '', prefix_sep=''
        )

    # Get total child
    print("Counting total children")
    total_child = df_User.groupby(by='UserID')[['ChildID']].nunique().reset_index()
    total_child.rename(
        columns={
            'ChildID':'TotalChild'
        }, inplace=True
    )

    # Get number of female and male children for each user
    print("Counting number of boy and girl seperate")
    no_fe_n_ma = df_User.pivot_table(index='UserID', columns='ChildGender', values='ChildID', aggfunc='count').reset_index()
    no_fe_n_ma.rename(
        columns={
            'female':'No.Female',
            'male': 'No.Male'
        }, inplace=True
    )
    no_fe_n_ma.fillna(0, inplace=True)

    # Get median age children
    print("Get median children age")
    age_child = df_User.groupby(by='UserID')[['Age']].median().reset_index()
    age_child.rename(
        columns={
            'Age':'MedianChildAge'
        }
    )

    # Rename certain columns to match with general database
    # df_Engagement['lastuse_byhour'] = df_Engagement['lastuse'].apply(lambda x: pd.to_datetime(x).strftime("%H:%M:%S"))
    df_Engagement.rename(
        columns={
            'open_time': 'Opentime',
            'payment_screen_time': 'PaymentScreenTime'
        }, inplace=True
    )

    # Acquire dataframe Engagement by condition
    # df_Engagement = df_Engagement[df_Engagement.nth_day_from_registration <=7]
    # df_Engagement = df_Engagement[condition]
    
    """
        Idea fromm: https://stackoverflow.com/questions/47360510/pandas-groupby-and-aggregation-output-should-include-all-the-original-columns-i
    """
    print("Obtain Users event base on condition")
    df_merge = df_Engagement.groupby(by=['UserID', 'EventDate', 'ActionType'], as_index=False).progress_apply(
        lambda x : x.sum() if ((x.dtypes=='int64') | (x.dtypes=='float64')).any() else x.head(1)
        )
    print('df_merge: \n',df_merge)
    # Retain labels and important features

    labels_df = df_merge[['UserID', 'cutoffDay', 'lateUser', 'Label']]

    # Create base df for merge
    print("Create base column for merge")
    based_df = df_Engagement.groupby('UserID', as_index=False).progress_apply(
        lambda x: x.head(1))[['UserID', 'UserJoinedDate']].reset_index(drop=True)
    print("Unique user: ", based_df.shape[0])

    # Total of Action/Events
    print("Get total Open time/Usage Time/Record/Payment screen time")
    total_merge = df_merge.groupby(by='UserID')[['Opentime', 'UsageTime', 'Records', 'PaymentScreenTime']].progress_apply(sum).reset_index()
    total_merge.rename(
        columns={'Opentime':'TotalOpentime', 'UsageTime':'TotalUsageTime', 
                'Records':'TotalRecords', 'PaymentScreenTime': 'TotalPayscreentime'}, inplace=True
    )

    # Sum activity merge
    print('Get Open time/Usage Time/Record/Payment screen time base on Action type')
    activity_merge = pd.pivot_table(df_merge, 
                                index='UserID', 
                                columns='ActionType', 
                                values=['Opentime', 'UsageTime', 'Records','PaymentScreenTime'],
                                aggfunc=np.sum)

    activity_merge.columns = ["".join((i,j.title())) for i,j in activity_merge.columns]
    activity_merge.reset_index(inplace=True)
    activity_merge.fillna(0, inplace=True)

    print("Get interest...")
    # map_func = np.vectorize(lambda x: interest_rate(df_Engagement, x))
    # interest_df = map_func(based_df['UserID'])
    interest_df = [interest_rate(df_Engagement, n) for n in tqdm(based_df['UserID'])]
    interest_df = pd.concat(interest_df, axis=0, ignore_index=True)
    
    print(interest_df)
    merge_dfs = [
        total_child, no_fe_n_ma, age_child, total_merge, activity_merge, interest_df, device_brand_df, labels_df
        ]
    
    print("Star merging....")
    for df in merge_dfs:
        df.reset_index(inplace=True, drop=True)
        based_df = based_df.merge(df, on='UserID', how='left')
        based_df.drop_duplicates(subset=['UserID'], keep='first', inplace=True, ignore_index=True)

    print("Total user with compress events: ", based_df.shape)
    return based_df
  
def getEvent_before_cutoff(df_events, cutOffDay=3):
    days_from_regis = df_events.groupby('UserID')[['nth_day_from_registration']].min().reset_index()
    days_from_regis.rename(
        columns={
            "nth_day_from_registration": "MinFirstDay"
        },inplace=True
    )
    days_from_regis['cutoffDay'] = days_from_regis.MinFirstDay + cutOffDay
    days_from_regis['lateUser'] = (days_from_regis['MinFirstDay'] > 0).astype(int)

    Engagement = df_events.merge(days_from_regis, on='UserID',how='left')
    Engagement = Engagement[
        (Engagement['cutoffDay'] - Engagement['nth_day_from_registration']) > 0
        ].reset_index(drop=True)
    Engagement['usedDays'] = Engagement['nth_day_from_registration'] - Engagement['MinFirstDay']
    return Engagement

def setLabel(df_events, df_Payment, markDay=30):
    df_events = df_events.merge(df_Payment[['UserID','gapday']], how='left', on='UserID')
    """
        If label = True -> User paid before markDay
        else -> Free user
    """
    df_events['Label'] = ((df_events['gapday'] - df_events['MinFirstDay']) <= markDay).astype(int)
    print("Total events with labels: ", df_events.shape)
    return df_events

Engagements = getEvent_before_cutoff(df_Engagement, cutOffDay=3)
Engagements = setLabel(Engagements, df_Payment, markDay=30)
list_dataframes = [
    df_User,
    Engagements,
    df_Payment
]
condition_df = create_dataframe(list_dataframes)
condition_df
print(condition_df)

save_path = os.path.join(
    df_path, "Dataset"
    )
os.makedirs(
    save_path, exist_ok=True
)
condition_df.to_csv(
    os.path.join(save_path, "3days_cutoff.csv"), index=False
)