"""Diagnostic same-month image correspondence, not proof of shared source flights."""
import argparse,json
from pathlib import Path
import numpy as np
import rasterio,cv2
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--recovered',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True);rows=[]
 for date,filename in [('201408','201408ddyw.tif'),('201508','201508ddyw.tif')]:
  p=next((args.source/'DOM').glob(date+'*'))
  with rasterio.open(p) as r:
   w,h=1200,1220;t=from_origin(r.bounds.left,r.bounds.top,(r.bounds.right-r.bounds.left)/w,(r.bounds.top-r.bounds.bottom)/h)
   with WarpedVRT(r,crs=32650,transform=t,width=w,height=h,resampling=Resampling.bilinear) as v:a=v.read([1,2,3]);ma=v.dataset_mask()>0
  with rasterio.open(args.recovered/filename) as r:
   with WarpedVRT(r,crs=32650,transform=t,width=w,height=h,resampling=Resampling.bilinear) as v:b=v.read([1,2,3]);mb=v.dataset_mask()>0
  a=np.moveaxis(np.clip(a,0,255).astype('uint8'),0,-1);b=np.moveaxis(np.clip(b,0,255).astype('uint8'),0,-1);m=ma&mb&np.any(a>0,axis=2)&np.any(b>0,axis=2)
  ga=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);gb=cv2.cvtColor(b,cv2.COLOR_RGB2GRAY);sift=cv2.SIFT_create(nfeatures=5000);ka,da=sift.detectAndCompute(ga,m.astype('uint8')*255);kb,db=sift.detectAndCompute(gb,m.astype('uint8')*255)
  matches=cv2.BFMatcher().knnMatch(da,db,k=2);good=[x for x,y in matches if x.distance<.65*y.distance]
  src=np.float32([ka[x.queryIdx].pt for x in good]);dst=np.float32([kb[x.trainIdx].pt for x in good]);H,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=3)
  row={'date':date,'public_file':p.name,'recovered_file':filename,'geographic_grid_gray_correlation':float(np.corrcoef(ga[m],gb[m])[0,1]),'sift_ratio_matches':len(good),'ransac_inliers':int(inliers.sum()) if inliers is not None else 0,'diagnostic_affine_on_downsampled_grid':H.tolist() if H is not None else None,'interpretation':'Same-month spatial imagery correspondence diagnostic; repeated persistent features and colour processing prevent proof of shared raw flights. Not independent ground validation.'};rows.append(row)
  cv2.imwrite(str(args.output/(date+'_public_recovered_comparison.jpg')),cv2.cvtColor(np.concatenate([a,b],axis=1),cv2.COLOR_RGB2BGR));print(row,flush=True)
 (args.output/'source_correspondence.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
