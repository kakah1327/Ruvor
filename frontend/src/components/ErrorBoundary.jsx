import { Component } from 'react';

export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="card">
          <h2>Algo quebrou ao renderizar esta página</h2>
          <p className="meta">{String(this.state.error.message || this.state.error)}</p>
          <div className="actions">
            <button type="button" className="btn" onClick={() => this.setState({ error: null })}>
              tentar novamente
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
