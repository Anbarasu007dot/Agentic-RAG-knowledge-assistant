import { Component } from 'react'

class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('The frontend could not render.', error, errorInfo)
  }

  render() {
    if (this.state.error) {
      return (
        <main className="app-shell">
          <div className="notice error app-error" role="alert">
            <strong>The application could not be displayed.</strong>
            <p>{this.state.error.message || 'Refresh the page and try again.'}</p>
          </div>
        </main>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
