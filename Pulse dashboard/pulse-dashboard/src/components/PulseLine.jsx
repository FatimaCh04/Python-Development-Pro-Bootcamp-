export default function PulseLine({ className = '', color = '#6C5CE7', height = 40 }) {
  return (
    <svg
      className={`pulse-divider ${className}`}
      viewBox="0 0 1400 40"
      preserveAspectRatio="none"
      style={{ height }}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M0,20 L120,20 L150,20 L170,4 L190,36 L210,10 L230,30 L250,20 L400,20
           L560,20 L590,20 L610,2 L630,38 L650,8 L670,32 L690,20 L900,20
           L1060,20 L1090,20 L1110,6 L1130,34 L1150,12 L1170,28 L1190,20 L1400,20"
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
