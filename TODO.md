# TODO: 

    Refactor __init__.py to remove redundant code and improve module structure

    Make this windows compliant

    Make sure we type all methods and add doc

    refactor ananlysis to basemodel to suport OpenAPI

    collect PNM files in case i have to work offline

    redo Analysis Request for all

        Basic Analysis (SNMP Data (Signal Analysis))
        {
            "mac_address": "0050.f112.dcc3",
            "ip_address" : "",
            snmp:{
                version:{
                    2:{
                        write_community:""
                    }
                }
            },            
            "analysis": {
                "analysis_type": 0
            }
        } 

        Basic Analysis (Single Shot Capture)
        {
            "mac_address": "0050.f112.dcc3",
            "ip_address" : "",
            snmp:{
                version:{
                    2:{
                        write_community:""
                    }
                }
            },            
            "analysis": {
                "analysis_type": 0
            }
        }    

        Advance Analysis (Post Captures, ussually Multi Capture)
        {
            "mac_address": "0050.f112.dcc3",
            "analysis": {
                "analysis_type": 0
            },
            "operation_id": "string"
        }

    Basic Modem Query (Request)
    {
        device:{
            mac_address:"",
            ip_address: "",
            snmp:{
                version:{
                    2:{
                        write_community:""
                    }
                }
            }
        }
    }

    Basic Modem Query with Basic Analysis (Request)
    {
        device:{
            mac_address:"",
            ip_address: "",
            snmp:{
                version:{
                    2:{
                        write_community:""
                    }
                }
            }
        },
        analysis: {
            analysis_parameters: {
                type:0,
            }            
        }        
    }    

    Basic Modem Query with Advance Analysis (Request)
    {
        device:{
            mac_address:"",
            ip_address: "",
            snmp:{
                version:{
                    2:{
                        write_community:""
                    }
                }
            }
        },
        analysis: {
            pnm_capture_parameters: {
                "measurement_duration": 1,
                "sample_interval": 1,           
            },
        }      
    }

    Basic Modem Query with Advance Analysis (Request)
    {
        device:{
            mac_address:"",
        },
        analysis: {
            pnm_capture_parameters: {
                retrival:{
                    operation_id:"" 
                }      
            },
            analysis_parameters: {
                type:0,            
            }                         
        }
    }


        