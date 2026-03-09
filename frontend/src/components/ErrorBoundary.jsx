import React from 'react'
import { t } from '../i18n'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('[CircuitAI] Uncaught error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-boundary-icon">⚠️</div>
          <h2>{t('errorBoundaryTitle') || 'Something went wrong'}</h2>
          <p className="error-boundary-msg">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button className="btn-primary" onClick={this.handleReset}>
            {t('retry') || 'Try Again'}
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
