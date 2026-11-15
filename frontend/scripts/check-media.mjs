import {chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const out=path.resolve('../deliverables');
const browser=await chromium.launch({channel:'msedge',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1260}});
 // Recapture subnet panels tightly so exported figures remain readable.
 await page.goto('http://127.0.0.1:5173/');await page.getByText('Backend connected').waitFor();
 await page.getByRole('button',{name:'Subnet calculator',exact:true}).click();await page.getByRole('button',{name:'Calculate subnet'}).click();await page.getByText('192.168.1.63',{exact:true}).waitFor();
 await page.locator('.app').screenshot({path:path.join(out,'screenshots/07-subnet-calculator.png')});
 await page.getByLabel('IPv4 address / prefix').fill('invalid');await page.getByRole('button',{name:'Calculate subnet'}).click();await page.getByRole('alert').waitFor();
 await page.locator('.app').screenshot({path:path.join(out,'screenshots/08-input-validation.png')});
 const html=path.join(out,'verification/video-check.html');
 await writeFile(html,'<html><body style="margin:0;background:black"><video id="v" src="'+pathToFileURL(path.join(out,'NetSim_Lite_Demo.webm')).href+'" style="width:100%;height:100vh" controls></video></body></html>');
 await page.goto(pathToFileURL(html).href);
 await page.waitForFunction(()=>document.querySelector('video').readyState>=2);
 const info=await page.evaluate(async()=>{const v=document.querySelector('video');v.currentTime=8;await new Promise(resolve=>v.addEventListener('seeked',resolve,{once:true}));return {durationSeconds:Number.isFinite(v.duration)?v.duration:null,width:v.videoWidth,height:v.videoHeight,decodeError:v.error?.message||null}});
 await page.screenshot({path:path.join(out,'verification/video-frame.png')});
 if(info.decodeError||info.width!==1440||info.height!==1260)throw Error('Video media verification failed');
 await writeFile(path.join(out,'verification/video-validation.json'),JSON.stringify(info,null,2));
 console.log(info);
}finally{await browser.close()}
