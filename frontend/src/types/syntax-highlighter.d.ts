declare module 'react-syntax-highlighter' {
  import { Component } from 'react'
  
  interface SyntaxHighlighterProps {
    language?: string
    style?: any
    children?: string
    PreTag?: string | React.ComponentType<any>
    className?: string
    [key: string]: any
  }
  
  export class Prism extends Component<SyntaxHighlighterProps> {}
  export default class SyntaxHighlighter extends Component<SyntaxHighlighterProps> {}
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  export const oneDark: any
  export const oneLight: any
}