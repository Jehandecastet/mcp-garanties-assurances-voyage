import Step1 from './Step1Client';

export default function Step1Wrapper() {
  return (
    <Step1 proxyUrl={process.env.NEXT_PUBLIC_INSTANTAIR_PROXY || ''} />
  );
}
