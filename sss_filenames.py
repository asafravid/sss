#################################################
# V44 - Author: Asaf Ravid <asaf.rvd@gmail.com> #
#################################################

def create_filenames_list(date_and_time):
    filename_csv_db                     = "{}/db.csv".format(date_and_time)
    filename_sss_engine                 = "{}/sss_engine.csv".format(date_and_time)
    filename_ssss_engine                = "{}/ssss_engine.csv".format(date_and_time)
    filename_sssss_engine               = "{}/sssss_engine.csv".format(date_and_time)
    filename_ssse_engine                = "{}/ssse_engine.csv".format(date_and_time)
    filename_sssse_engine               = "{}/sssse_engine.csv".format(date_and_time)
    filename_ssssse_engine              = "{}/ssssse_engine.csv".format(date_and_time)
    filename_sss_engine_no_div          = "{}/sss_engine_no_div.csv".format(date_and_time)
    filename_ssss_engine_no_div         = "{}/ssss_engine_no_div.csv".format(date_and_time)
    filename_sssss_engine_no_div        = "{}/sssss_engine_no_div.csv".format(date_and_time)
    filename_ssse_engine_no_div         = "{}/ssse_engine_no_div.csv".format(date_and_time)
    filename_sssse_engine_no_div        = "{}/sssse_engine_no_div.csv".format(date_and_time)
    filename_ssssse_engine_no_div       = "{}/ssssse_engine_no_div.csv".format(date_and_time)
    filename_sss_engine_only_div        = "{}/sss_engine_only_div.csv".format(date_and_time)
    filename_ssss_engine_only_div       = "{}/ssss_engine_only_div.csv".format(date_and_time)
    filename_sssss_engine_only_div      = "{}/sssss_engine_only_div.csv".format(date_and_time)
    filename_ssse_engine_only_div       = "{}/ssse_engine_only_div.csv".format(date_and_time)
    filename_sssse_engine_only_div      = "{}/sssse_engine_only_div.csv".format(date_and_time)
    filename_ssssse_engine_only_div     = "{}/ssssse_engine_only_div.csv".format(date_and_time)
    filename_sssi_engine                = "{}/sssi_engine.csv".format(date_and_time)
    filename_ssssi_engine               = "{}/ssssi_engine.csv".format(date_and_time)
    filename_sssssi_engine              = "{}/sssssi_engine.csv".format(date_and_time)
    filename_sssei_engine               = "{}/sssei_engine.csv".format(date_and_time)
    filename_ssssei_engine              = "{}/ssssei_engine.csv".format(date_and_time)
    filename_sssssei_engine             = "{}/sssssei_engine.csv".format(date_and_time)
    filename_sssi_engine_no_div         = "{}/sssi_engine_no_div.csv".format(date_and_time)
    filename_ssssi_engine_no_div        = "{}/ssssi_engine_no_div.csv".format(date_and_time)
    filename_sssssi_engine_no_div       = "{}/sssssi_engine_no_div.csv".format(date_and_time)
    filename_sssei_engine_no_div        = "{}/sssei_engine_no_div.csv".format(date_and_time)
    filename_ssssei_engine_no_div       = "{}/ssssei_engine_no_div.csv".format(date_and_time)
    filename_sssssei_engine_no_div      = "{}/sssssei_engine_no_div.csv".format(date_and_time)
    filename_sssi_engine_only_div       = "{}/sssi_engine_only_div.csv".format(date_and_time)
    filename_ssssi_engine_only_div      = "{}/ssssi_engine_only_div.csv".format(date_and_time)
    filename_sssssi_engine_only_div     = "{}/sssssi_engine_only_div.csv".format(date_and_time)
    filename_sssei_engine_only_div      = "{}/sssei_engine_only_div.csv".format(date_and_time)
    filename_ssssei_engine_only_div     = "{}/ssssei_engine_only_div.csv".format(date_and_time)
    filename_sssssei_engine_only_div    = "{}/sssssei_engine_only_div.csv".format(date_and_time)

    filename_sssss_best_engine          = "{}/sssss_best_engine.csv".format(date_and_time)
    filename_sssss_best_no_div_engine   = "{}/sssss_best_no_div_engine.csv".format(date_and_time)
    filename_sssss_best_only_div_engine = "{}/sssss_best_only_div_engine.csv".format(date_and_time)

    filenames_list = [
        filename_csv_db,
        filename_sss_engine                ,    filename_ssss_engine               ,    filename_sssss_engine              ,    filename_ssse_engine               ,
        filename_sssse_engine              ,    filename_ssssse_engine             ,    filename_sss_engine_no_div         ,    filename_ssss_engine_no_div        ,
        filename_sssss_engine_no_div       ,    filename_ssse_engine_no_div        ,    filename_sssse_engine_no_div       ,    filename_ssssse_engine_no_div      ,
        filename_sss_engine_only_div       ,    filename_ssss_engine_only_div      ,    filename_sssss_engine_only_div     ,    filename_ssse_engine_only_div      ,
        filename_sssse_engine_only_div     ,    filename_ssssse_engine_only_div    ,    filename_sssi_engine               ,    filename_ssssi_engine              ,
        filename_sssssi_engine             ,    filename_sssei_engine              ,    filename_ssssei_engine             ,    filename_sssssei_engine            ,
        filename_sssi_engine_no_div        ,    filename_ssssi_engine_no_div       ,    filename_sssssi_engine_no_div      ,    filename_sssei_engine_no_div       ,
        filename_ssssei_engine_no_div      ,    filename_sssssei_engine_no_div     ,    filename_sssi_engine_only_div      ,    filename_ssssi_engine_only_div     ,
        filename_sssssi_engine_only_div    ,    filename_sssei_engine_only_div     ,    filename_ssssei_engine_only_div    ,    filename_sssssei_engine_only_div   ,
        filename_sssss_best_engine         ,    filename_sssss_best_no_div_engine  ,    filename_sssss_best_only_div_engine
    ]
    return filenames_list
