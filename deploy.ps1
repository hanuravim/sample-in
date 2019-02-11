#Error preferences
$WarningPreference = "SilentlyContinue"
$ErrorActionPreference = "Stop"
#endregion


Login-AzureRmAccount
$Subscription              = Get-AzureRmSubscription | Out-GridView -Title "Select the Azure subscription..." -PassThru
Select-AzureRmSubscription -SubscriptionId $Subscription.SubscriptionId

$SPTenant = ''
$CertThumbprint = ''
$SPAppID = ''


Login-AzureRmAccount -ServicePrincipal -TenantId $SPTenant -Credential $CertThumbprint -ApplicationId $SPAppID


$applicationId = "";
$securePassword = "" | ConvertTo-SecureString -AsPlainText -Force
$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $applicationId, $securePassword
Connect-AzureRmAccount -ServicePrincipal -Credential $credential -TenantId ""



#region Parameters
$RG_Name_aks=      'GAV-NE-INE-NP-QA-ARM-POC'
$locationaks=     'northeurope'
$RG_Namelog=      'GAV-NE-INE-NP-QA-LOG-ARM-POC'
$locationlog=     'eastus'


$paramUri=    'C:\Users\503090627\Desktop\Personal\ARM\CoolStuff\in\pmaster.parameteres.qa.json'

$masterTemplateUri=  'C:\Users\503090627\Desktop\Personal\ARM\CoolStuff\in\master.json'

#Check or Create Resource group
Get-AzureRmResourceGroup -Name $RG_Name_aks -ev notPresentaks -ea 0
if ($notPresentaks) { Write-Host "Failover RG '$RG_Name' does not exist.Creating new in $locationaks..." -ForegroundColor Yellow
New-AzureRmResourceGroup -Name $RG_Name_aks -Location $locationaks
} else { Write-Host "Using existing resource group '$RG_Name_aks'"-ForegroundColor Yellow ;}

Get-AzureRmResourceGroup -Name $RG_Namelog -ev notPresentlog -ea 0
if ($notPresentlog) { Write-Host "Failover RG '$RG_Namelog' does not exist.Creating new in $locationlog..." -ForegroundColor Yellow
New-AzureRmResourceGroup -Name $RG_Namelog -Location $locationlog
} else { Write-Host "Using existing resource group '$RG_Namelog'"-ForegroundColor Yellow ;}

#region deploy
New-AzureRmResourceGroupDeployment -ResourceGroupName $RG_Name_aks -Mode Incremental -TemplateParameterFile $paramUri -TemplateUri $masterTemplateUri -Verbose
#endregion

(Get-AzureRmContext).Subscription


#$virtualNetwork = New-AzureRmVirtualNetwork `
  #-ResourceGroupName GAV-INE-QA-TEST-RG `
 # -Location northeurope `
  #-Name vnetarmdemo `
  #-AddressPrefix 10.0.0.0/16