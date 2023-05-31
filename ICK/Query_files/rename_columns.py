import pandas as pd
import os

list_csv_path = [
    '/Users/admin/_Work/Data/icanKID/df_Payment.csv',
    '/Users/admin/_Work/Data/icanKID/df_User.csv',
    '/Users/admin/_Work/Data/icanKID/df_Engagement.csv',
    '/Users/admin/_Work/Data/icanKID/df_User_Child_DeviceBrand.csv',
    '/Users/admin/_Work/Data/icanKID/df_Engagement_detail_learn.csv'
]
list_names = [
    ['UserID',
    'UserJoinedDate','firstpay','firstPaymentType','gapday','Amount','TransactionNo','avgValue'],
    ['UserID','ChildBday','ChildGender'],
    ['EventDate','UserID','ActionType','UserJoinedDate','nth_day_from_registration','open_time',
     'payment_screen_time','DeviceBrand','UsageTime','Records','lastuse', 'firstuse'],
    ['UserID','ChildID','ChildBday','ChildGender','DeviceBrand'],
    ['EventDate','nth_day_from_registration','UserID','SubjectName','IsCompleted','UsageTime','Records']
]
for i,path in enumerate(list_csv_path):
    csv_path = path
    df = pd.read_csv(csv_path)
    df.rename(columns={str(i):col for i, col in enumerate(list_names[i])}, inplace=True)

    df.to_csv(csv_path, index=False)
    print(df)