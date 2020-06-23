#Story: Script which runs in the background as a windows service monitoring for suspicious acticity

#Write a function to be continuously running and checking for new changes
function monitor() {
    
    $pc_name = $env:COMPUTERNAME
    #get the current time to avoid the system pulling all previous logs
    $date = Get-Date

    #continuous loop to check for security violations
    while ($true) {

        $date_old = Get-Date
        #Get the most recent event logs
        
        $Filter = @{
                Logname = 'Security'
                ID = 4732,4740,4756,4635,4625,4648
                StartTime = $date
        }

        $check = Get-WinEvent -FilterHashtable $Filter -ErrorAction Ignore | Select MachineName,TimeCreated,LogName,ProviderName,ID,Message
        
        #reset the date as soon as it finishes to pull all events since 
        $date = $date_old
        
        #If statement to check if the $check variable has been filled
        if ($check -ne $null) {
            
            #set the date for file format
            $file_date = Get-Date
            $date_fix = $file_date.ToUniversalTime().ToString("yyyy-MM-dd HH-mm-ss")

            #Push the event log to a json file
            #Make sure to set a location for log files below and on line 53
            $check | ConvertTo-Json -Depth 100 | out-file "C:\Users\**USERNAME_HERE**\Documents\ZigZag_Logs\$pc_name-$date_fix.json"
          
            sleep 20

        } else {
            
            sleep 20

        }


    }
}

function monitor2() {

    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = 'C:\Users\**USERNAME_HERE**\Documents\ZigZag_Logs'
    $watcher.EnableRaisingEvents = $true

    $action =
    {
        $path = $event.SourceEventArgs.FullPath

        #First path below is the location of private key, linking to public key on your deployer's backend authorized keys

        scp -i C:\Users\**USERNAME_HERE**\.ssh\id_rsa -o "StrictHostKeyChecking=no" $path deployer@techx.daniel.hellstern.org:/home/deployer/notify2/logs
    }

    Register-ObjectEvent $watcher 'Created' -Action $action
    
}
monitor2
monitor