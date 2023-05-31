from clickhouse_driver import connect
import pandas as pd
import os

save_path = '/Users/admin/_Work/Data/icanKID'
name_list = ["Payment","User", 'Engagement','User_DeviceBrand','Engagement_detail_learn']
query_list =[
    """
        with payment as (
        select a.UserID, firstpay, PaymentType as firstPayment, Amount, TransactionNo, avgValue
        from (select UserID , min(CreatedAt) as firstpay, sum(FinalValue) as Amount, count(*) as TransactionNo, sum(FinalValue)/count(*) as avgValue
        from user_subscription_records
        where TransactionType = 'purchase'
        and TransactionStatus = 'succeed'
        and RefundTransactionID is NULL
        and PlanID in (select PlanID from subscription_plan_profile where PlanIsTrial = 0)
        group by UserID ) a 
        join user_subscription_records b on a.UserID = b.UserID and a.firstpay = b.CreatedAt )

        select UserID , 
        UserJoinedDate ,
        firstpay,
        firstPayment,
        case when dateDiff('day', UserJoinedDate , firstpay) < 0 then null else dateDiff('day', UserJoinedDate , firstpay) end as gapday,
        Amount,
        TransactionNo,
        avgValue
        from user_profile 
        left join payment on payment.UserID = user_profile.UserID
        where date(UserJoinedDate )>='2022-04-01'
        and date(UserJoinedDate )<='2023-04-20'
    """,
    """
        select UserID ,
        ChildBday ,
        ChildGender 
        from user_profile user 
        join child_profile child on child.UserID = user.UserID 
        where date(UserJoinedDate )>='2022-04-01'
        and date(UserJoinedDate )<='2023-04-20'
    """,
    """
        with logs as (
        select date(EventTime) as EventDate ,
        UserID ,
        max(DeviceBrand) as DeviceBrand,
        sum(case when EventCode = 'app_info_openApp' then 1 else 0 end) as open_time,
        sum(case when EventCode in ( 'pop_up_show_listSub', 'parentcontrol_show_listPackage') then 1 else 0 end) as payment_screen_time 
        from (select * from user_event_logs union all select * from user_event_logs_arXiv )
        group by EventDate, UserID)

        select date(records.EventTime) as EventDate,
        records.UserID as UserID,
        ActionType,
        user.UserJoinedDate as UserJoinedDate,
        datediff('day', UserJoinedDate, EventTime) as nth_day_from_registration,
        open_time,
        payment_screen_time,
        DeviceBrand,
        round(sum(UsageTime )/60,2) as UsageTime,
        count(*) as Records,
        max(records.EventTime) as lastuse,
        min(records.EventTime) as firstuse
        from (select * from view_child_usage_records union all select * from view_child_usage_records_arXiv) records 
        join user_profile user on user.UserID = records.UserID 
        left join logs on logs.UserID = records.UserID and logs.EventDate = date(records.EventTime) 
        where date(UserJoinedDate) >= '2022-04-01' 
        and date(UserJoinedDate) <= '2023-04-20'
        group by EventDate , UserID , ActionType , UserJoinedDate, nth_day_from_registration, open_time, payment_screen_time,
        DeviceBrand
    """,
    """
        select DISTINCT user.UserID , ChildID,
        ChildBday ,
        ChildGender, 
        DeviceBrand
        from user_profile user 
        join child_profile child on child.UserID = user.UserID 
        left join (select DISTINCT UserID ,
        DeviceBrand, DeviceModel  
        from (select * 
        from user_event_logs_arXiv
        union all
        select * 
        from user_event_logs)) brands on brands.UserID = user.UserID
        where date(UserJoinedDate )>= '2022-04-01'
        and date(UserJoinedDate )<='2023-04-20'
    """,
    """
        select date(EventTime) as EventDate,
        datediff('day',UserJoinedDate, EventTime) as nthday_from_registration,
        records.UserID,
        SubjectName,
        IsCompleted,
        round(sum(UsageTime)/60,2) as UsageTime,
        count(*) as Records
        from (select * from view_child_usage_records_arXiv union all select * from view_child_usage_records) records 
        join activity_profile act on act.ActivityID = records.ActivityID 
        join user_profile pro on pro.UserID = records.UserID
        where date(UserJoinedDate)>='2022-04-01' and date(UserJoinedDate)<='2023-04-20'
        group by EventDate,
        nthday_from_registration,
        records.UserID,
        SubjectName,
        IsCompleted
        order by records.UserID , EventDate, SubjectName , IsCompleted 
    """
]
def crawl_data(queries, names):
    conn = connect(
        host='10.100.1.73',
        port=29000, 
        user='admin', 
        password='admin@123', 
        database='icankid'
        )
    cursor = conn.cursor()
    for i,query in enumerate(queries):
        print(f"Crawling {names[i]} data")
        cursor.execute(query)
        result = cursor.fetchall()
        df = pd.DataFrame(result)

        df.to_csv(
            os.path.join(
            save_path, f"df_{names[i]}.csv"
            ), index=False
        )
        print(df.shape)

    conn.close()

crawl_data([query_list[-1]], [name_list[-1]])