const React = require('react');
const { render, screen } = require('@testing-library/react');

function Card(props) {
  return React.createElement(
    'div',
    null,
    React.createElement('div', null, props.title),
    React.createElement('div', null, String(props.value))
  );
}

describe('Admin Card', () => {
  it('renders title and value', async () => {
    render(React.createElement(Card, { title: 'Агенты', value: 3 }));
    expect(screen.getByText('Агенты')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});


