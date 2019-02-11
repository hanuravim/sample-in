Param (
  [Parameter()]
  [String]$SourceSAKey='UJ0R68SXTvS9Q3JRkLKCTp0LNR89xD6HUV2glXm+rebcGef0cNs135ZvgbIoE/tP5Am640z1FIokgRfxODa45w==',
  [String]$SAName='bitnamijenkinsdiag'
)
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module Azure -Confirm:$False
Import-Module Azure
$storageContext = New-AzureStorageContext -StorageAccountName $SAName -StorageAccountKey $SourceSAKey
$storageContext |  New-AzureStorageShare -Name 'bitnamijenkinsdiag'
